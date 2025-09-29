use crate::types::*;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use log::{error, info, warn};
use std::collections::HashMap;
use std::process::{Child, Command, Stdio};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use tokio::time::{sleep, Duration};
use uuid::Uuid;

#[async_trait]
pub trait ProcessManager: Send + Sync {
    async fn start_service(&self, name: &str) -> Result<Uuid>;
    async fn stop_service(&self, name: &str) -> Result<()>;
    async fn restart_service(&self, name: &str) -> Result<()>;
    async fn get_service_status(&self, name: &str) -> Result<ServiceState>;
    async fn get_all_services(&self) -> Result<ServiceRegistry>;
    async fn register_service(&self, config: ServiceConfig) -> Result<()>;
}

pub struct LocalProcessManager {
    pub services: Arc<RwLock<ServiceRegistry>>,
    processes: Arc<RwLock<HashMap<String, Child>>>,
}

impl LocalProcessManager {
    pub fn new() -> Self {
        Self {
            services: Arc::new(RwLock::new(HashMap::new())),
            processes: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn initialize_default_services(&self) -> Result<()> {
        let services = vec![
            ServiceConfig {
                name: "ai-engine".to_string(),
                path: "python3".to_string(),
                args: vec!["-m".to_string(), "uvicorn".to_string(), "main:app".to_string(), "--reload".to_string()],
                port: Some(8000),
                health_endpoint: Some("/health".to_string()),
                startup_timeout: 30,
                restart_policy: RestartPolicy::Always,
            },
            ServiceConfig {
                name: "dsl-parser".to_string(),
                path: "dsl-parser".to_string(),
                args: vec!["--server".to_string()],
                port: Some(8001),
                health_endpoint: Some("/health".to_string()),
                startup_timeout: 10,
                restart_policy: RestartPolicy::Always,
            },
            ServiceConfig {
                name: "graph-engine".to_string(),
                path: "./main".to_string(),
                args: vec!["--port".to_string(), "8002".to_string()],
                port: Some(8002),
                health_endpoint: Some("/health".to_string()),
                startup_timeout: 15,
                restart_policy: RestartPolicy::Always,
            },
            ServiceConfig {
                name: "event-processor".to_string(),
                path: "elixir".to_string(),
                args: vec!["-S".to_string(), "mix".to_string(), "phx.server".to_string()],
                port: Some(8003),
                health_endpoint: Some("/health".to_string()),
                startup_timeout: 20,
                restart_policy: RestartPolicy::Always,
            },
        ];

        for service in services {
            self.register_service(service).await?;
        }

        Ok(())
    }

    async fn spawn_process(&self, config: &ServiceConfig) -> Result<Child> {
        let mut cmd = Command::new(&config.path);
        cmd.args(&config.args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        if let Some(port) = config.port {
            cmd.env("PORT", port.to_string());
        }

        let child = cmd.spawn().map_err(|e| {
            anyhow!("Failed to spawn process for {}: {}", config.name, e)
        })?;

        info!("Started process for service: {}", config.name);
        Ok(child)
    }

    async fn update_service_status(&self, name: &str, status: ServiceStatus) -> Result<()> {
        let mut services = self.services.write().await;
        if let Some(service) = services.get_mut(name) {
            service.status = status.clone();
            if let ServiceStatus::Running = status {
                service.start_time = Some(
                    SystemTime::now()
                        .duration_since(UNIX_EPOCH)?
                        .as_secs()
                );
            }
        }
        Ok(())
    }
}

#[async_trait]
impl ProcessManager for LocalProcessManager {
    async fn register_service(&self, config: ServiceConfig) -> Result<()> {
        let service_state = ServiceState {
            id: Uuid::new_v4(),
            config: config.clone(),
            status: ServiceStatus::Stopped,
            pid: None,
            start_time: None,
            restart_count: 0,
            last_error: None,
        };

        let mut services = self.services.write().await;
        services.insert(config.name.clone(), service_state);
        info!("Registered service: {}", config.name);
        Ok(())
    }

    async fn start_service(&self, name: &str) -> Result<Uuid> {
        let config = {
            let services = self.services.read().await;
            services
                .get(name)
                .ok_or_else(|| anyhow!("Service not found: {}", name))?
                .config
                .clone()
        };

        self.update_service_status(name, ServiceStatus::Starting).await?;

        match self.spawn_process(&config).await {
            Ok(child) => {
                let pid = child.id();
                let mut processes = self.processes.write().await;
                processes.insert(name.to_string(), child);
                
                // Update service state
                let mut services = self.services.write().await;
                if let Some(service) = services.get_mut(name) {
                    service.pid = Some(pid);
                    service.status = ServiceStatus::Running;
                }

                info!("Service {} started with PID: {}", name, pid);
                Ok(services.get(name).unwrap().id)
            }
            Err(e) => {
                error!("Failed to start service {}: {}", name, e);
                self.update_service_status(name, ServiceStatus::Failed).await?;
                
                let mut services = self.services.write().await;
                if let Some(service) = services.get_mut(name) {
                    service.last_error = Some(e.to_string());
                }
                
                Err(e)
            }
        }
    }

    async fn stop_service(&self, name: &str) -> Result<()> {
        let mut processes = self.processes.write().await;
        if let Some(mut child) = processes.remove(name) {
            child.kill()?;
            info!("Stopped service: {}", name);
        }

        self.update_service_status(name, ServiceStatus::Stopped).await?;
        Ok(())
    }

    async fn restart_service(&self, name: &str) -> Result<()> {
        info!("Restarting service: {}", name);
        self.stop_service(name).await?;
        sleep(Duration::from_secs(2)).await;
        
        let mut services = self.services.write().await;
        if let Some(service) = services.get_mut(name) {
            service.restart_count += 1;
        }
        drop(services);

        self.start_service(name).await?;
        Ok(())
    }

    async fn get_service_status(&self, name: &str) -> Result<ServiceState> {
        let services = self.services.read().await;
        services
            .get(name)
            .cloned()
            .ok_or_else(|| anyhow!("Service not found: {}", name))
    }

    async fn get_all_services(&self) -> Result<ServiceRegistry> {
        let services = self.services.read().await;
        Ok(services.clone())
    }
}
