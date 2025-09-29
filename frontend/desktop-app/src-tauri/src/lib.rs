mod bridge;
mod health;
mod ipc;
mod memory;
mod process;
mod tests;
mod types;

use bridge::{initialize_ocaml_bridge, parse_dsl, compile_dsl, CompileRequest, ParseResult, CompileResult};
use health::{HealthChecker, HttpHealthChecker};
use ipc::IpcManager;
use process::{LocalProcessManager, ProcessManager};
use std::sync::Arc;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            // Initialize process manager
            let process_manager = Arc::new(LocalProcessManager::new());
            let pm_clone = Arc::clone(&process_manager);
            
            // Initialize health checker
            let services = Arc::clone(&process_manager.services);
            let health_checker = Arc::new(HttpHealthChecker::new(services));
            let hc_clone = Arc::clone(&health_checker);
            
            // Initialize IPC manager
            let ipc_manager = Arc::new(IpcManager::new());
            let ipc_clone = Arc::clone(&ipc_manager);

            // Initialize OCaml bridge
            if let Err(e) = initialize_ocaml_bridge() {
                log::error!("Failed to initialize OCaml bridge: {}", e);
            } else {
                log::info!("OCaml bridge initialized successfully");
            }

            // Store managers in app state
            app.manage(process_manager as Arc<dyn ProcessManager>);
            app.manage(health_checker as Arc<dyn HealthChecker>);
            app.manage(ipc_manager);

            // Initialize services asynchronously
            tauri::async_runtime::spawn(async move {
                if let Err(e) = pm_clone.initialize_default_services().await {
                    log::error!("Failed to initialize default services: {}", e);
                }
                
                if let Err(e) = ipc_clone.initialize().await {
                    log::error!("Failed to initialize IPC manager: {}", e);
                }
                
                hc_clone.start_monitoring().await;
                log::info!("All services initialized");
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            ipc::send_ipc_message,
            ipc::get_service_status,
            ipc::start_service,
            ipc::stop_service,
            ipc::restart_service,
            ipc::get_all_services,
            ipc::get_health_status,
            parse_personality,
            compile_personality,
            validate_personality,
            get_parser_version
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// OCaml Bridge Tauri Commands

#[tauri::command]
pub async fn parse_personality(dsl_content: String, filename: Option<String>) -> Result<ParseResult, String> {
    let filename_ref = filename.as_deref();
    parse_dsl(&dsl_content, filename_ref).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn compile_personality(request: CompileRequest) -> Result<CompileResult, String> {
    compile_dsl(request).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn validate_personality(personality: bridge::PersonalityData) -> Result<Vec<String>, String> {
    bridge::OCAML_BRIDGE.validate_personality(&personality).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn get_parser_version() -> Result<String, String> {
    bridge::OCAML_BRIDGE.get_parser_version().map_err(|e| e.to_string())
}
