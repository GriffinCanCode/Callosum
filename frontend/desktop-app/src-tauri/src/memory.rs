use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex, RwLock};
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;
use thiserror::Error;

const MAX_INLINE_SIZE: usize = 1024; // 1KB threshold for inline vs shared memory
const SHARED_MEMORY_TTL: u64 = 300; // 5 minutes TTL for shared memory blocks

#[derive(Debug, Error)]
pub enum MemoryError {
    #[error("Shared memory block not found: {0}")]
    BlockNotFound(Uuid),
    #[error("Memory block expired: {0}")]
    BlockExpired(Uuid),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    #[error("Memory allocation error: {0}")]
    AllocationError(String),
    #[error("Access denied for memory block: {0}")]
    AccessDenied(Uuid),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessageData {
    Inline(Vec<u8>),
    SharedRef(SharedMemoryRef),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SharedMemoryRef {
    pub block_id: Uuid,
    pub size: usize,
    pub checksum: u64,
    pub expires_at: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: Uuid,
    pub sender: String,
    pub recipient: String,
    pub method: String,
    pub data: MessageData,
    pub timestamp: u64,
    pub priority: MessagePriority,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MessagePriority {
    Low,
    Normal,
    High,
    Critical,
}

#[derive(Debug)]
struct SharedMemoryBlock {
    data: Vec<u8>,
    created_at: u64,
    accessed_at: u64,
    access_count: u64,
    owner: String,
}

pub struct SharedMemoryManager {
    blocks: Arc<RwLock<HashMap<Uuid, SharedMemoryBlock>>>,
    cleanup_interval: u64,
}

impl SharedMemoryManager {
    pub fn new() -> Self {
        let manager = Self {
            blocks: Arc::new(RwLock::new(HashMap::new())),
            cleanup_interval: 60, // Cleanup every minute
        };
        
        // Start cleanup task
        manager.start_cleanup_task();
        manager
    }

    pub fn allocate_block(&self, data: Vec<u8>, owner: &str) -> Result<SharedMemoryRef, MemoryError> {
        let block_id = Uuid::new_v4();
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|_| MemoryError::AllocationError("System time error".into()))?
            .as_secs();

        let checksum = self.calculate_checksum(&data);
        let size = data.len();

        let block = SharedMemoryBlock {
            data,
            created_at: now,
            accessed_at: now,
            access_count: 0,
            owner: owner.to_string(),
        };

        let mut blocks = self.blocks.write().unwrap();
        blocks.insert(block_id, block);

        Ok(SharedMemoryRef {
            block_id,
            size,
            checksum,
            expires_at: now + SHARED_MEMORY_TTL,
        })
    }

    pub fn read_block(&self, block_ref: &SharedMemoryRef) -> Result<Vec<u8>, MemoryError> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        if now > block_ref.expires_at {
            return Err(MemoryError::BlockExpired(block_ref.block_id));
        }

        let mut blocks = self.blocks.write().unwrap();
        let block = blocks.get_mut(&block_ref.block_id)
            .ok_or(MemoryError::BlockNotFound(block_ref.block_id))?;

        // Verify checksum
        let checksum = self.calculate_checksum(&block.data);
        if checksum != block_ref.checksum {
            return Err(MemoryError::AllocationError("Data corruption detected".into()));
        }

        // Update access stats
        block.accessed_at = now;
        block.access_count += 1;

        Ok(block.data.clone())
    }

    pub fn deallocate_block(&self, block_id: Uuid) -> Result<(), MemoryError> {
        let mut blocks = self.blocks.write().unwrap();
        blocks.remove(&block_id)
            .ok_or(MemoryError::BlockNotFound(block_id))?;
        Ok(())
    }

    pub fn get_memory_stats(&self) -> MemoryStats {
        let blocks = self.blocks.read().unwrap();
        let total_blocks = blocks.len();
        let total_size: usize = blocks.values().map(|b| b.data.len()).sum();
        let average_access: f64 = blocks.values()
            .map(|b| b.access_count)
            .sum::<u64>() as f64 / total_blocks.max(1) as f64;

        MemoryStats {
            total_blocks,
            total_size,
            average_access_count: average_access,
        }
    }

    fn calculate_checksum(&self, data: &[u8]) -> u64 {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        
        let mut hasher = DefaultHasher::new();
        data.hash(&mut hasher);
        hasher.finish()
    }

    fn start_cleanup_task(&self) {
        let blocks = Arc::clone(&self.blocks);
        let cleanup_interval = self.cleanup_interval;
        
        tokio::spawn(async move {
            let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(cleanup_interval));
            
            loop {
                interval.tick().await;
                
                let now = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs();
                
                let mut blocks_guard = blocks.write().unwrap();
                let expired_keys: Vec<Uuid> = blocks_guard
                    .iter()
                    .filter(|(_, block)| block.created_at + SHARED_MEMORY_TTL < now)
                    .map(|(id, _)| *id)
                    .collect();
                
                for key in expired_keys {
                    blocks_guard.remove(&key);
                }
                
                log::debug!("Cleaned up {} expired memory blocks", blocks_guard.len());
            }
        });
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryStats {
    pub total_blocks: usize,
    pub total_size: usize,
    pub average_access_count: f64,
}

pub struct MessagePassingSystem {
    memory_manager: SharedMemoryManager,
    message_handlers: Arc<RwLock<HashMap<String, Box<dyn MessageHandler + Send + Sync>>>>,
}

pub trait MessageHandler: Send + Sync {
    fn handle_message(&self, message: Message) -> Result<Message, MemoryError>;
}

impl MessagePassingSystem {
    pub fn new() -> Self {
        Self {
            memory_manager: SharedMemoryManager::new(),
            message_handlers: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub fn create_message(
        &self,
        sender: &str,
        recipient: &str,
        method: &str,
        data: Vec<u8>,
        priority: MessagePriority,
    ) -> Result<Message, MemoryError> {
        let message_id = Uuid::new_v4();
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let message_data = if data.len() > MAX_INLINE_SIZE {
            // Use shared memory for large data
            let shared_ref = self.memory_manager.allocate_block(data, sender)?;
            MessageData::SharedRef(shared_ref)
        } else {
            // Inline small data
            MessageData::Inline(data)
        };

        Ok(Message {
            id: message_id,
            sender: sender.to_string(),
            recipient: recipient.to_string(),
            method: method.to_string(),
            data: message_data,
            timestamp: now,
            priority,
        })
    }

    pub fn send_message(&self, message: Message) -> Result<(), MemoryError> {
        // In a real implementation, this would route to the appropriate service
        log::debug!("Sending message {} from {} to {}", message.id, message.sender, message.recipient);
        
        // For now, just validate that we can read the data
        self.get_message_data(&message)?;
        Ok(())
    }

    pub fn get_message_data(&self, message: &Message) -> Result<Vec<u8>, MemoryError> {
        match &message.data {
            MessageData::Inline(data) => Ok(data.clone()),
            MessageData::SharedRef(shared_ref) => {
                self.memory_manager.read_block(shared_ref)
            }
        }
    }

    pub fn cleanup_message(&self, message: &Message) -> Result<(), MemoryError> {
        if let MessageData::SharedRef(shared_ref) = &message.data {
            self.memory_manager.deallocate_block(shared_ref.block_id)?;
        }
        Ok(())
    }

    pub fn register_handler<H>(&self, method: &str, handler: H) 
    where 
        H: MessageHandler + Send + Sync + 'static 
    {
        let mut handlers = self.message_handlers.write().unwrap();
        handlers.insert(method.to_string(), Box::new(handler));
    }

    pub fn get_memory_stats(&self) -> MemoryStats {
        self.memory_manager.get_memory_stats()
    }
}

// Example handler for OCaml bridge messages
pub struct OcamlMessageHandler;

impl MessageHandler for OcamlMessageHandler {
    fn handle_message(&self, message: Message) -> Result<Message, MemoryError> {
        log::info!("Handling OCaml message: {} -> {}", message.method, message.recipient);
        
        // Process the message data through OCaml bridge
        let _data = match &message.data {
            MessageData::Inline(data) => data.clone(),
            MessageData::SharedRef(shared_ref) => {
                // Read from shared memory
                vec![] // Placeholder
            }
        };
        
        // Create response message
        Ok(Message {
            id: Uuid::new_v4(),
            sender: message.recipient,
            recipient: message.sender,
            method: format!("{}_response", message.method),
            data: MessageData::Inline(b"success".to_vec()),
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            priority: message.priority,
        })
    }
}

// Global instance for message passing
lazy_static::lazy_static! {
    pub static ref MESSAGE_SYSTEM: MessagePassingSystem = MessagePassingSystem::new();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_shared_memory_allocation() {
        let manager = SharedMemoryManager::new();
        let data = vec![1, 2, 3, 4, 5];
        
        let shared_ref = manager.allocate_block(data.clone(), "test").unwrap();
        let read_data = manager.read_block(&shared_ref).unwrap();
        
        assert_eq!(data, read_data);
    }

    #[test]
    fn test_message_creation() {
        let system = MessagePassingSystem::new();
        let small_data = vec![1, 2, 3];
        let large_data = vec![0; 2048]; // Larger than MAX_INLINE_SIZE
        
        let small_msg = system.create_message("sender", "recipient", "test", small_data, MessagePriority::Normal).unwrap();
        let large_msg = system.create_message("sender", "recipient", "test", large_data, MessagePriority::Normal).unwrap();
        
        assert!(matches!(small_msg.data, MessageData::Inline(_)));
        assert!(matches!(large_msg.data, MessageData::SharedRef(_)));
    }
}
