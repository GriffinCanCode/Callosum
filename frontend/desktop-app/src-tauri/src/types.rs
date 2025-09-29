use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceConfig {
    pub name: String,
    pub path: String,
    pub args: Vec<String>,
    pub port: Option<u16>,
    pub health_endpoint: Option<String>,
    pub startup_timeout: u64,
    pub restart_policy: RestartPolicy,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RestartPolicy {
    Never,
    Always,
    OnFailure,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ServiceStatus {
    Stopped,
    Starting,
    Running,
    Failed,
    Restarting,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceState {
    pub id: Uuid,
    pub config: ServiceConfig,
    pub status: ServiceStatus,
    pub pid: Option<u32>,
    pub start_time: Option<u64>,
    pub restart_count: u32,
    pub last_error: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthCheckResult {
    pub service_id: Uuid,
    pub healthy: bool,
    pub latency: Option<u64>,
    pub error: Option<String>,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IpcMessage {
    pub id: Uuid,
    pub service: String,
    pub method: String,
    pub payload: serde_json::Value,
    pub timestamp: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IpcResponse {
    pub request_id: Uuid,
    pub success: bool,
    pub data: Option<serde_json::Value>,
    pub error: Option<String>,
}

pub type ServiceRegistry = HashMap<String, ServiceState>;
