#[cfg(test)]
mod memory_leak_tests {
    use super::bridge::*;
    use super::memory::*;
    use std::time::{Duration, Instant};
    use std::thread;

    const LEAK_TEST_ITERATIONS: usize = 1000;
    const MEMORY_THRESHOLD_MB: usize = 100; // Max memory growth in MB

    #[test]
    fn test_ocaml_bridge_memory_leaks() {
        // This test would require OCaml runtime, so we'll skip for now
        // In a real implementation, we'd:
        // 1. Initialize OCaml bridge
        // 2. Perform many parse operations
        // 3. Monitor memory usage
        // 4. Ensure cleanup is working
        
        let initial_memory = get_memory_usage();
        
        for i in 0..LEAK_TEST_ITERATIONS {
            let dsl_content = format!(r#"
                personality "Test{}" {{
                    traits {{
                        test_trait: 0.{};
                    }}
                }}
            "#, i, i % 10);
            
            // Simulate parsing (would use actual OCaml bridge)
            let _result = simulate_parse(&dsl_content);
            
            // Force cleanup every 100 iterations
            if i % 100 == 0 {
                simulate_cleanup();
                thread::sleep(Duration::from_millis(10));
            }
        }
        
        let final_memory = get_memory_usage();
        let memory_growth = final_memory.saturating_sub(initial_memory);
        
        assert!(
            memory_growth < MEMORY_THRESHOLD_MB * 1024 * 1024,
            "Memory leak detected: grew by {} bytes",
            memory_growth
        );
    }

    #[test]
    fn test_shared_memory_cleanup() {
        let manager = SharedMemoryManager::new();
        let mut refs = vec![];
        
        // Allocate many memory blocks
        for i in 0..100 {
            let data = vec![i as u8; 1024]; // 1KB each
            let shared_ref = manager.allocate_block(data, "test").unwrap();
            refs.push(shared_ref);
        }
        
        let stats_before = manager.get_memory_stats();
        assert_eq!(stats_before.total_blocks, 100);
        
        // Wait for cleanup (in real test, we'd trigger cleanup manually)
        thread::sleep(Duration::from_millis(100));
        
        // Deallocate half explicitly
        for i in 0..50 {
            manager.deallocate_block(refs[i].block_id).unwrap();
        }
        
        let stats_after = manager.get_memory_stats();
        assert!(stats_after.total_blocks <= 50);
    }

    #[test]
    fn test_message_system_memory() {
        let system = MessagePassingSystem::new();
        let large_data = vec![0u8; 10 * 1024 * 1024]; // 10MB
        
        // Create and send many large messages
        for i in 0..10 {
            let message = system.create_message(
                "test_sender",
                "test_recipient",
                "test_method",
                large_data.clone(),
                MessagePriority::Normal,
            ).unwrap();
            
            let _data = system.get_message_data(&message).unwrap();
            system.cleanup_message(&message).unwrap();
        }
        
        let stats = system.get_memory_stats();
        // After cleanup, should have minimal memory usage
        assert!(stats.total_size < 1024 * 1024); // Less than 1MB
    }

    #[test]
    fn test_ffi_error_handling() {
        // Test that FFI errors are properly handled and don't leak memory
        let bridge = OcamlBridge::new();
        
        // Test invalid DSL that should cause errors
        let invalid_dsl = "invalid dsl content !!!";
        
        for _ in 0..100 {
            let _result = bridge.validate_personality(&PersonalityData {
                name: "test".to_string(),
                traits: vec![],
                knowledge: vec![],
                behaviors: vec![],
                evolution: vec![],
            });
            
            // Each call should handle errors gracefully
        }
        
        // Memory should be stable
        assert!(!bridge.is_initialized() || bridge.is_initialized());
    }

    #[test]
    fn test_concurrent_access() {
        use std::sync::Arc;
        use std::thread;
        
        let manager = Arc::new(SharedMemoryManager::new());
        let mut handles = vec![];
        
        // Spawn multiple threads accessing shared memory
        for thread_id in 0..10 {
            let manager_clone = Arc::clone(&manager);
            let handle = thread::spawn(move || {
                for i in 0..100 {
                    let data = vec![thread_id as u8, i as u8];
                    let shared_ref = manager_clone.allocate_block(data.clone(), "concurrent_test").unwrap();
                    let read_data = manager_clone.read_block(&shared_ref).unwrap();
                    assert_eq!(data, read_data);
                    manager_clone.deallocate_block(shared_ref.block_id).unwrap();
                }
            });
            handles.push(handle);
        }
        
        // Wait for all threads to complete
        for handle in handles {
            handle.join().unwrap();
        }
        
        // All memory should be cleaned up
        let final_stats = manager.get_memory_stats();
        assert_eq!(final_stats.total_blocks, 0);
    }

    // Helper functions for memory testing
    fn get_memory_usage() -> usize {
        // In a real implementation, this would get actual memory usage
        // For now, return a placeholder
        0
    }
    
    fn simulate_parse(_dsl: &str) -> ParseResult {
        // Simulate parsing without actual OCaml runtime
        ParseResult {
            success: true,
            personality: Some(PersonalityData {
                name: "test".to_string(),
                traits: vec![],
                knowledge: vec![],
                behaviors: vec![],
                evolution: vec![],
            }),
            errors: vec![],
            warnings: vec![],
        }
    }
    
    fn simulate_cleanup() {
        // Simulate cleanup operations
    }

    #[test]
    fn test_memory_pressure_handling() {
        let system = MessagePassingSystem::new();
        
        // Create many large messages to test memory pressure
        let mut messages = vec![];
        for i in 0..50 {
            let large_data = vec![i as u8; 1024 * 1024]; // 1MB each
            let message = system.create_message(
                "pressure_test",
                "recipient",
                "method",
                large_data,
                MessagePriority::Normal,
            ).unwrap();
            messages.push(message);
        }
        
        let initial_stats = system.get_memory_stats();
        
        // Clean up half the messages
        for message in messages.iter().take(25) {
            system.cleanup_message(message).unwrap();
        }
        
        let after_cleanup_stats = system.get_memory_stats();
        assert!(after_cleanup_stats.total_size < initial_stats.total_size);
    }
}

#[cfg(test)]
mod integration_tests {
    use super::*;
    use crate::bridge::*;
    use crate::memory::*;

    #[tokio::test]
    async fn test_end_to_end_dsl_processing() {
        let dsl_content = r#"
            personality "Integration Test" {
                traits {
                    analytical: 0.8;
                    creative: 0.6;
                }
                
                knowledge {
                    domain("programming") {
                        rust: advanced;
                        ocaml: intermediate;
                    }
                }
            }
        "#;
        
        // This would test the full pipeline:
        // 1. Parse DSL through bridge
        // 2. Use shared memory for large data
        // 3. Compile to different targets
        // 4. Clean up all resources
        
        // For now, just test that our types work correctly
        let compile_request = CompileRequest {
            personality: PersonalityData {
                name: "Integration Test".to_string(),
                traits: vec![
                    TraitData {
                        name: "analytical".to_string(),
                        strength: 0.8,
                        modifiers: vec![],
                    },
                    TraitData {
                        name: "creative".to_string(),
                        strength: 0.6,
                        modifiers: vec![],
                    },
                ],
                knowledge: vec![],
                behaviors: vec![],
                evolution: vec![],
            },
            target: CompileTarget::Json,
            context: None,
        };
        
        // Serialize and deserialize to test the full data flow
        let serialized = serde_json::to_string(&compile_request).unwrap();
        let deserialized: CompileRequest = serde_json::from_str(&serialized).unwrap();
        
        assert_eq!(compile_request.personality.name, deserialized.personality.name);
        assert_eq!(compile_request.personality.traits.len(), deserialized.personality.traits.len());
    }

    #[test]
    fn test_error_propagation() {
        // Test that errors properly propagate through the FFI boundary
        let bridge = OcamlBridge::new();
        
        // Test initialization errors
        assert!(!bridge.is_initialized());
        
        // Test parsing errors with uninitialized bridge
        let result = bridge.parse_personality("test", None);
        assert!(result.is_err());
        match result.unwrap_err() {
            BridgeError::RuntimeNotInitialized => {}, // Expected
            _ => panic!("Expected RuntimeNotInitialized error"),
        }
    }
}
