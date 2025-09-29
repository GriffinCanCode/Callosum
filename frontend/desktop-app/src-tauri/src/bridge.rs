use ocaml::{Runtime, Value};
use ocaml_sys::{caml_main, caml_startup};
use serde::{Deserialize, Serialize};
use std::ffi::CString;
use std::os::raw::c_char;
use std::sync::{Arc, Mutex, Once};
use anyhow::{anyhow, Result};
use thiserror::Error;

static INIT: Once = Once::new();
static RUNTIME: Mutex<Option<Runtime>> = Mutex::new(None);

#[derive(Debug, Error)]
pub enum BridgeError {
    #[error("OCaml runtime not initialized")]
    RuntimeNotInitialized,
    #[error("OCaml execution error: {0}")]
    ExecutionError(String),
    #[error("Serialization error: {0}")]
    SerializationError(#[from] serde_json::Error),
    #[error("FFI error: {0}")]
    FfiError(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParseResult {
    pub success: bool,
    pub personality: Option<PersonalityData>,
    pub errors: Vec<ParseError>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonalityData {
    pub name: String,
    pub traits: Vec<TraitData>,
    pub knowledge: Vec<KnowledgeDomain>,
    pub behaviors: Vec<BehaviorRule>,
    pub evolution: Vec<EvolutionRule>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraitData {
    pub name: String,
    pub strength: f64,
    pub modifiers: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeDomain {
    pub name: String,
    pub topics: Vec<TopicData>,
    pub connections: Vec<ConnectionData>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TopicData {
    pub name: String,
    pub level: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionData {
    pub from_domain: String,
    pub to_domain: String,
    pub strength: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BehaviorRule {
    pub condition: String,
    pub action: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvolutionRule {
    pub trigger: String,
    pub effect: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParseError {
    pub message: String,
    pub line: i32,
    pub column: i32,
    pub filename: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompileRequest {
    pub personality: PersonalityData,
    pub target: CompileTarget,
    pub context: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CompileTarget {
    Json,
    Lua,
    Prompt,
    Sql,
    Cypher,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompileResult {
    pub success: bool,
    pub output: Option<String>,
    pub errors: Vec<String>,
}

pub struct OcamlBridge {
    initialized: Arc<Mutex<bool>>,
}

impl OcamlBridge {
    pub fn new() -> Self {
        Self {
            initialized: Arc::new(Mutex::new(false)),
        }
    }

    pub fn initialize(&self) -> Result<(), BridgeError> {
        INIT.call_once(|| {
            // Initialize OCaml runtime
            let argv = vec![CString::new("callosum").unwrap()];
            let argv_ptr: Vec<*mut c_char> = argv.iter().map(|s| s.as_ptr() as *mut c_char).collect();
            
            unsafe {
                caml_startup(argv_ptr.as_ptr() as *mut *mut c_char);
            }

            // Create runtime instance
            let runtime = Runtime::init();
            let mut runtime_guard = RUNTIME.lock().unwrap();
            *runtime_guard = Some(runtime);
        });

        let mut initialized = self.initialized.lock().unwrap();
        *initialized = true;
        Ok(())
    }

    pub fn is_initialized(&self) -> bool {
        *self.initialized.lock().unwrap()
    }

    pub fn parse_personality(&self, dsl_content: &str, filename: Option<&str>) -> Result<ParseResult, BridgeError> {
        if !self.is_initialized() {
            return Err(BridgeError::RuntimeNotInitialized);
        }

        let runtime_guard = RUNTIME.lock().unwrap();
        let runtime = runtime_guard.as_ref().ok_or(BridgeError::RuntimeNotInitialized)?;

        // Convert Rust string to OCaml value
        let dsl_value = Value::string(dsl_content);
        let filename_value = match filename {
            Some(f) => Value::string(f),
            None => Value::string("<string>"),
        };

        // Call OCaml parsing function
        let result = runtime.call2("Dsl_parser.Ast.parse_personality_from_string", dsl_value, filename_value)
            .map_err(|e| BridgeError::ExecutionError(format!("OCaml parsing failed: {:?}", e)))?;

        // Convert OCaml result to Rust
        self.convert_parse_result(result)
    }

    pub fn compile_personality(&self, request: CompileRequest) -> Result<CompileResult, BridgeError> {
        if !self.is_initialized() {
            return Err(BridgeError::RuntimeNotInitialized);
        }

        let runtime_guard = RUNTIME.lock().unwrap();
        let runtime = runtime_guard.as_ref().ok_or(BridgeError::RuntimeNotInitialized)?;

        // Convert Rust data to OCaml values
        let personality_json = serde_json::to_string(&request.personality)?;
        let personality_value = Value::string(&personality_json);
        
        let target_value = match request.target {
            CompileTarget::Json => Value::string("Json"),
            CompileTarget::Lua => Value::string("Lua"),
            CompileTarget::Prompt => Value::string("Prompt"),
            CompileTarget::Sql => Value::string("Sql"),
            CompileTarget::Cypher => Value::string("Cypher"),
        };

        let context_value = match request.context {
            Some(ctx) => Value::some(Value::string(&ctx)),
            None => Value::none(),
        };

        // Call OCaml compilation function
        let result = runtime.call3("Dsl_parser.Compiler.compile", personality_value, target_value, context_value)
            .map_err(|e| BridgeError::ExecutionError(format!("OCaml compilation failed: {:?}", e)))?;

        self.convert_compile_result(result)
    }

    fn convert_parse_result(&self, ocaml_result: Value) -> Result<ParseResult, BridgeError> {
        // Check if result is Ok or Error variant
        if ocaml_result.tag() == 0 { // Ok variant
            let personality = ocaml_result.field(0);
            let personality_data = self.convert_personality(personality)?;
            
            Ok(ParseResult {
                success: true,
                personality: Some(personality_data),
                errors: vec![],
                warnings: vec![],
            })
        } else { // Error variant
            let errors = ocaml_result.field(0);
            let parse_errors = self.convert_errors(errors)?;
            
            Ok(ParseResult {
                success: false,
                personality: None,
                errors: parse_errors,
                warnings: vec![],
            })
        }
    }

    fn convert_personality(&self, personality: Value) -> Result<PersonalityData, BridgeError> {
        // Extract fields from OCaml personality record
        let name = personality.field(0).string_val()
            .map_err(|_| BridgeError::FfiError("Failed to extract personality name".into()))?
            .to_string();

        // For now, return minimal data - this would be expanded to parse all fields
        Ok(PersonalityData {
            name,
            traits: vec![],
            knowledge: vec![],
            behaviors: vec![],
            evolution: vec![],
        })
    }

    fn convert_errors(&self, errors: Value) -> Result<Vec<ParseError>, BridgeError> {
        let mut parse_errors = vec![];
        
        // Convert OCaml list to Vec
        let mut current = errors;
        while current.tag() != 0 { // Not empty list
            let error = current.field(0);
            let message = error.field(0).string_val()
                .map_err(|_| BridgeError::FfiError("Failed to extract error message".into()))?
                .to_string();
            
            // Extract location info (simplified for now)
            parse_errors.push(ParseError {
                message,
                line: 1,
                column: 1,
                filename: "<unknown>".to_string(),
            });
            
            current = current.field(1); // Move to next element
        }
        
        Ok(parse_errors)
    }

    fn convert_compile_result(&self, ocaml_result: Value) -> Result<CompileResult, BridgeError> {
        if ocaml_result.tag() == 0 { // Ok variant
            let output = ocaml_result.field(0).string_val()
                .map_err(|_| BridgeError::FfiError("Failed to extract compilation output".into()))?
                .to_string();
            
            Ok(CompileResult {
                success: true,
                output: Some(output),
                errors: vec![],
            })
        } else { // Error variant
            Ok(CompileResult {
                success: false,
                output: None,
                errors: vec!["Compilation failed".to_string()],
            })
        }
    }

    pub fn validate_personality(&self, personality: &PersonalityData) -> Result<Vec<String>, BridgeError> {
        if !self.is_initialized() {
            return Err(BridgeError::RuntimeNotInitialized);
        }

        let mut warnings = vec![];
        
        // Basic validation (would be expanded)
        if personality.name.is_empty() {
            warnings.push("Personality name is empty".to_string());
        }
        
        for trait_data in &personality.traits {
            if trait_data.strength < 0.0 || trait_data.strength > 1.0 {
                warnings.push(format!("Trait {} has invalid strength: {}", trait_data.name, trait_data.strength));
            }
        }
        
        Ok(warnings)
    }

    pub fn get_parser_version(&self) -> Result<String, BridgeError> {
        if !self.is_initialized() {
            return Err(BridgeError::RuntimeNotInitialized);
        }

        Ok("0.1.0".to_string()) // Would extract from OCaml
    }

    pub fn cleanup(&self) -> Result<(), BridgeError> {
        let mut initialized = self.initialized.lock().unwrap();
        *initialized = false;
        
        // Additional cleanup would go here
        Ok(())
    }
}

// Singleton instance for global access
lazy_static::lazy_static! {
    pub static ref OCAML_BRIDGE: Arc<OcamlBridge> = Arc::new(OcamlBridge::new());
}

// Safe initialization function
pub fn initialize_ocaml_bridge() -> Result<(), BridgeError> {
    OCAML_BRIDGE.initialize()
}

// Convenience functions for external use
pub fn parse_dsl(content: &str, filename: Option<&str>) -> Result<ParseResult, BridgeError> {
    OCAML_BRIDGE.parse_personality(content, filename)
}

pub fn compile_dsl(request: CompileRequest) -> Result<CompileResult, BridgeError> {
    OCAML_BRIDGE.compile_personality(request)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bridge_initialization() {
        let bridge = OcamlBridge::new();
        assert!(!bridge.is_initialized());
        
        // Note: actual initialization would require OCaml runtime
        // This is a placeholder test structure
    }

    #[test]
    fn test_validation() {
        let personality = PersonalityData {
            name: "Test".to_string(),
            traits: vec![TraitData {
                name: "test_trait".to_string(),
                strength: 1.5, // Invalid strength
                modifiers: vec![],
            }],
            knowledge: vec![],
            behaviors: vec![],
            evolution: vec![],
        };

        let bridge = OcamlBridge::new();
        let warnings = bridge.validate_personality(&personality).unwrap();
        assert!(!warnings.is_empty());
    }
}
