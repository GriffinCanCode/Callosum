use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    // Only rebuild if OCaml files change
    println!("cargo:rerun-if-changed=../../../backend/personality/dsl-parser/lib");
    println!("cargo:rerun-if-changed=../../../backend/personality/dsl-parser/bin");
    
    // Build OCaml DSL parser
    build_ocaml_dsl_parser();
    
    // Link OCaml runtime and compiled objects
    link_ocaml_runtime();
    
    // Continue with Tauri build
    tauri_build::build()
}

fn build_ocaml_dsl_parser() {
    let ocaml_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .join("../../../backend/personality/dsl-parser");
    
    println!("Building OCaml DSL parser in {:?}", ocaml_dir);
    
    // Build with dune
    let output = Command::new("dune")
        .args(&["build", "--profile", "release"])
        .current_dir(&ocaml_dir)
        .output();
    
    match output {
        Ok(output) => {
            if !output.status.success() {
                println!("cargo:warning=OCaml build failed: {}", String::from_utf8_lossy(&output.stderr));
                // Don't fail the build - allow development without OCaml
            } else {
                println!("cargo:info=OCaml DSL parser built successfully");
            }
        }
        Err(e) => {
            println!("cargo:warning=Failed to run dune build: {}", e);
            println!("cargo:warning=Continuing build without OCaml support");
        }
    }
}

fn link_ocaml_runtime() {
    // Get OCaml configuration
    let ocaml_config = get_ocaml_config();
    
    if let Some(config) = ocaml_config {
        // Add OCaml library search paths
        for lib_path in &config.lib_paths {
            println!("cargo:rustc-link-search=native={}", lib_path);
        }
        
        // Link OCaml runtime libraries
        for lib in &config.libraries {
            println!("cargo:rustc-link-lib=static={}", lib);
        }
        
        // Link system libraries required by OCaml
        println!("cargo:rustc-link-lib=dylib=m");      // Math library
        println!("cargo:rustc-link-lib=dylib=pthread"); // Pthread library
        
        #[cfg(target_os = "linux")]
        {
            println!("cargo:rustc-link-lib=dylib=dl");  // Dynamic loading library
        }
        
        #[cfg(target_os = "macos")]
        {
            println!("cargo:rustc-link-lib=framework=CoreFoundation");
        }
    } else {
        println!("cargo:warning=OCaml configuration not found, compiling without OCaml support");
    }
}

struct OcamlConfig {
    lib_paths: Vec<String>,
    libraries: Vec<String>,
}

fn get_ocaml_config() -> Option<OcamlConfig> {
    // Try to get OCaml configuration
    let output = Command::new("ocaml-config").output();
    
    match output {
        Ok(output) if output.status.success() => {
            let config_str = String::from_utf8_lossy(&output.stdout);
            parse_ocaml_config(&config_str)
        }
        _ => {
            // Fallback: try common locations
            get_default_ocaml_config()
        }
    }
}

fn parse_ocaml_config(config_str: &str) -> Option<OcamlConfig> {
    let mut lib_paths = vec![];
    let mut libraries = vec!["camlrun", "unix", "str"].into_iter().map(String::from).collect::<Vec<_>>();
    
    for line in config_str.lines() {
        if line.starts_with("standard_library: ") {
            let path = line.replace("standard_library: ", "");
            lib_paths.push(path);
        }
    }
    
    if lib_paths.is_empty() {
        None
    } else {
        Some(OcamlConfig { lib_paths, libraries })
    }
}

fn get_default_ocaml_config() -> Option<OcamlConfig> {
    // Common OCaml installation paths
    let common_paths = vec![
        "/usr/lib/ocaml",
        "/usr/local/lib/ocaml",
        "/opt/homebrew/lib/ocaml",
        "~/.opam/default/lib/ocaml",
    ];
    
    for path in common_paths {
        let expanded_path = if path.starts_with("~") {
            if let Ok(home) = env::var("HOME") {
                path.replace("~", &home)
            } else {
                continue;
            }
        } else {
            path.to_string()
        };
        
        if PathBuf::from(&expanded_path).exists() {
            return Some(OcamlConfig {
                lib_paths: vec![expanded_path],
                libraries: vec!["camlrun".to_string(), "unix".to_string(), "str".to_string()],
            });
        }
    }
    
    None
}

// Additional helper to check if OCaml development is available
fn check_ocaml_development() -> bool {
    Command::new("ocaml").arg("-version").output().is_ok() &&
    Command::new("dune").arg("--version").output().is_ok()
}