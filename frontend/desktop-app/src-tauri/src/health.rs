use crate::types::*;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use log::{error, info, warn};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;
use tokio::time::{interval, sleep};
use uuid::Uuid;

#[async_trait]
pub trait HealthChecker: Send + Sync {
    async fn check_service(&self, service_id: Uuid) -> Result<HealthCheckResult>;
    async fn check_all_services(&self) -> Result<Vec<HealthCheckResult>>;
    async fn start_monitoring(&self);
    async fn stop_monitoring(&self);
    async fn get_health_history(&self, service_id: Uuid) -> Result<Vec<HealthCheckResult>>;
}

pub struct HttpHealthChecker {
    services: Arc<RwLock<ServiceRegistry>>,
    health_history: Arc<RwLock<HashMap<Uuid, Vec<HealthCheckResult>>>>,
    monitoring_active: Arc<RwLock<bool>>,
    client: reqwest::Client,
}

impl HttpHealthChecker {
    pub fn new(services: Arc<RwLock<ServiceRegistry>>) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
            .expect("Failed to create HTTP client");

        Self {
            services,
            health_history: Arc::new(RwLock::new(HashMap::new())),
            monitoring_active: Arc::new(RwLock::new(false)),
            client,
        }
    }

    async fn perform_http_check(&self, config: &ServiceConfig) -> Result<(bool, Option<u64>)> {
        if let (Some(port), Some(endpoint)) = (config.port, &config.health_endpoint) {
            let url = format!("http://localhost:{}{}", port, endpoint);
            let start = Instant::now();

            match self.client.get(&url).send().await {
                Ok(response) => {
                    let latency = start.elapsed().as_millis() as u64;
                    let healthy = response.status().is_success();
                    Ok((healthy, Some(latency)))
                }
                Err(e) => {
                    warn!("Health check failed for {}: {}", config.name, e);
                    Ok((false, None))
                }
            }
        } else {
            // Fallback to process-based check
            Ok((true, None)) // Assume healthy if process is running
        }
    }

    async fn store_health_result(&self, result: HealthCheckResult) {
        let mut history = self.health_history.write().await;
        let service_history = history.entry(result.service_id).or_insert_with(Vec::new);
        
        service_history.push(result);
        
        // Keep only last 100 results per service
        if service_history.len() > 100 {
            service_history.remove(0);
        }
    }

    async fn monitoring_loop(&self) {
        let mut interval = interval(Duration::from_secs(30)); // Check every 30 seconds

        loop {
            interval.tick().await;
            
            let monitoring_active = *self.monitoring_active.read().await;
            if !monitoring_active {
                break;
            }

            match self.check_all_services().await {
                Ok(results) => {
                    for result in results {
                        if !result.healthy {
                            warn!(
                                "Service {} is unhealthy: {:?}",
                                result.service_id, result.error
                            );
                        }
                        self.store_health_result(result).await;
                    }
                }
                Err(e) => {
                    error!("Error during health check cycle: {}", e);
                }
            }
        }
    }

    fn get_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs()
    }
}

#[async_trait]
impl HealthChecker for HttpHealthChecker {
    async fn check_service(&self, service_id: Uuid) -> Result<HealthCheckResult> {
        let services = self.services.read().await;
        let service = services
            .values()
            .find(|s| s.id == service_id)
            .ok_or_else(|| anyhow!("Service not found"))?;

        let timestamp = Self::get_timestamp();

        // Basic status check
        if let ServiceStatus::Failed | ServiceStatus::Stopped = service.status {
            return Ok(HealthCheckResult {
                service_id,
                healthy: false,
                latency: None,
                error: Some("Service is not running".to_string()),
                timestamp,
            });
        }

        // HTTP health check
        match self.perform_http_check(&service.config).await {
            Ok((healthy, latency)) => Ok(HealthCheckResult {
                service_id,
                healthy,
                latency,
                error: if healthy { None } else { Some("HTTP check failed".to_string()) },
                timestamp,
            }),
            Err(e) => Ok(HealthCheckResult {
                service_id,
                healthy: false,
                latency: None,
                error: Some(e.to_string()),
                timestamp,
            }),
        }
    }

    async fn check_all_services(&self) -> Result<Vec<HealthCheckResult>> {
        let services = self.services.read().await;
        let mut results = Vec::new();

        for service in services.values() {
            match self.check_service(service.id).await {
                Ok(result) => results.push(result),
                Err(e) => {
                    error!("Failed to check service {}: {}", service.id, e);
                    results.push(HealthCheckResult {
                        service_id: service.id,
                        healthy: false,
                        latency: None,
                        error: Some(e.to_string()),
                        timestamp: Self::get_timestamp(),
                    });
                }
            }
        }

        Ok(results)
    }

    async fn start_monitoring(&self) {
        info!("Starting health monitoring");
        *self.monitoring_active.write().await = true;
        
        let self_clone = Arc::new(HttpHealthChecker {
            services: Arc::clone(&self.services),
            health_history: Arc::clone(&self.health_history),
            monitoring_active: Arc::clone(&self.monitoring_active),
            client: self.client.clone(),
        });

        tokio::spawn(async move {
            self_clone.monitoring_loop().await;
        });
    }

    async fn stop_monitoring(&self) {
        info!("Stopping health monitoring");
        *self.monitoring_active.write().await = false;
    }

    async fn get_health_history(&self, service_id: Uuid) -> Result<Vec<HealthCheckResult>> {
        let history = self.health_history.read().await;
        Ok(history
            .get(&service_id)
            .cloned()
            .unwrap_or_default())
    }
}
