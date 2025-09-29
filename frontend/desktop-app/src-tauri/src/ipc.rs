use crate::types::*;
use anyhow::{anyhow, Result};
use log::{error, info};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tauri::{AppHandle, Emitter, Manager, State, Window};
use tokio::sync::{mpsc, RwLock};
use uuid::Uuid;

pub struct IpcManager {
    pending_requests: Arc<RwLock<HashMap<Uuid, mpsc::UnboundedSender<IpcResponse>>>>,
    service_clients: Arc<RwLock<HashMap<String, reqwest::Client>>>,
}

impl IpcManager {
    pub fn new() -> Self {
        Self {
            pending_requests: Arc::new(RwLock::new(HashMap::new())),
            service_clients: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn initialize(&self) -> Result<()> {
        let client = reqwest::Client::new();
        let mut clients = self.service_clients.write().await;
        
        // Initialize HTTP clients for each service
        clients.insert("ai-engine".to_string(), client.clone());
        clients.insert("dsl-parser".to_string(), client.clone());
        clients.insert("graph-engine".to_string(), client.clone());
        clients.insert("event-processor".to_string(), client.clone());
        
        Ok(())
    }

    pub async fn send_message(&self, message: IpcMessage) -> Result<IpcResponse> {
        let (tx, mut rx) = mpsc::unbounded_channel();
        
        // Store the pending request
        self.pending_requests.write().await.insert(message.id, tx);
        
        // Forward message to appropriate service
        self.forward_to_service(&message).await?;
        
        // Wait for response with timeout
        tokio::select! {
            response = rx.recv() => {
                self.pending_requests.write().await.remove(&message.id);
                response.ok_or_else(|| anyhow!("Response channel closed"))
            }
            _ = tokio::time::sleep(tokio::time::Duration::from_secs(30)) => {
                self.pending_requests.write().await.remove(&message.id);
                Err(anyhow!("Request timeout"))
            }
        }
    }

    async fn forward_to_service(&self, message: &IpcMessage) -> Result<()> {
        let clients = self.service_clients.read().await;
        let client = clients
            .get(&message.service)
            .ok_or_else(|| anyhow!("Service client not found: {}", message.service))?;

        let port = self.get_service_port(&message.service);
        let url = format!("http://localhost:{}/api/{}", port, message.method);
        
        let request_payload = serde_json::json!({
            "id": message.id,
            "data": message.payload
        });

        match client.post(&url).json(&request_payload).send().await {
            Ok(response) => {
                if response.status().is_success() {
                    match response.json::<Value>().await {
                        Ok(data) => {
                            let ipc_response = IpcResponse {
                                request_id: message.id,
                                success: true,
                                data: Some(data),
                                error: None,
                            };
                            self.send_response(ipc_response).await;
                        }
                        Err(e) => {
                            let ipc_response = IpcResponse {
                                request_id: message.id,
                                success: false,
                                data: None,
                                error: Some(format!("Failed to parse response: {}", e)),
                            };
                            self.send_response(ipc_response).await;
                        }
                    }
                } else {
                    let error_msg = format!("Service returned error: {}", response.status());
                    let ipc_response = IpcResponse {
                        request_id: message.id,
                        success: false,
                        data: None,
                        error: Some(error_msg),
                    };
                    self.send_response(ipc_response).await;
                }
            }
            Err(e) => {
                error!("Failed to send request to {}: {}", message.service, e);
                let ipc_response = IpcResponse {
                    request_id: message.id,
                    success: false,
                    data: None,
                    error: Some(e.to_string()),
                };
                self.send_response(ipc_response).await;
            }
        }

        Ok(())
    }

    async fn send_response(&self, response: IpcResponse) {
        if let Some(sender) = self.pending_requests.read().await.get(&response.request_id) {
            if sender.send(response).is_err() {
                error!("Failed to send response to pending request");
            }
        }
    }

    fn get_service_port(&self, service: &str) -> u16 {
        match service {
            "ai-engine" => 8000,
            "dsl-parser" => 8001,
            "graph-engine" => 8002,
            "event-processor" => 8003,
            _ => 8000,
        }
    }
}

// Tauri command handlers
#[tauri::command]
pub async fn send_ipc_message(
    message: IpcMessage,
    ipc_manager: State<'_, Arc<IpcManager>>,
) -> Result<IpcResponse, String> {
    ipc_manager
        .send_message(message)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_service_status(
    service_name: String,
    process_manager: State<'_, Arc<dyn crate::process::ProcessManager>>,
) -> Result<ServiceState, String> {
    process_manager
        .get_service_status(&service_name)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn start_service(
    service_name: String,
    process_manager: State<'_, Arc<dyn crate::process::ProcessManager>>,
) -> Result<String, String> {
    match process_manager.start_service(&service_name).await {
        Ok(service_id) => Ok(service_id.to_string()),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
pub async fn stop_service(
    service_name: String,
    process_manager: State<'_, Arc<dyn crate::process::ProcessManager>>,
) -> Result<(), String> {
    process_manager
        .stop_service(&service_name)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn restart_service(
    service_name: String,
    process_manager: State<'_, Arc<dyn crate::process::ProcessManager>>,
) -> Result<(), String> {
    process_manager
        .restart_service(&service_name)
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_all_services(
    process_manager: State<'_, Arc<dyn crate::process::ProcessManager>>,
) -> Result<ServiceRegistry, String> {
    process_manager
        .get_all_services()
        .await
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_health_status(
    service_id: String,
    health_checker: State<'_, Arc<dyn crate::health::HealthChecker>>,
) -> Result<HealthCheckResult, String> {
    let uuid = Uuid::parse_str(&service_id).map_err(|e| e.to_string())?;
    health_checker
        .check_service(uuid)
        .await
        .map_err(|e| e.to_string())
}

pub fn create_ipc_message(service: &str, method: &str, payload: Value) -> IpcMessage {
    IpcMessage {
        id: Uuid::new_v4(),
        service: service.to_string(),
        method: method.to_string(),
        payload,
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs(),
    }
}
