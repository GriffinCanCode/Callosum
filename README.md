# Callosum Personality DSL

A powerful Domain Specific Language for defining AI personalities with sophisticated traits, knowledge domains, behaviors, and evolution patterns.

## Overview

The Personality DSL enables declarative definition of AI personalities that can evolve over time, with:

- **Traits** with strength modifiers (decay, amplification, context conditions)
- **Knowledge domains** with expertise levels and inter-domain connections  
- **Behavioral rules** triggered by conditions
- **Evolution specifications** for personality growth

## Quick Start

### Installation

```bash
# Install OCaml dependencies
opam install . --deps-only

# Build
dune build

# Run tests
dune runtest
```

### Basic Usage

```ocaml
personality "Creative Developer" {
  traits {
    creativity: 0.9 with decay(0.05/month), unless("stressed");
    analytical: 0.7 with amplifies("problem_solving", 1.2);
    curiosity: 0.8 with when("learning");
  }
  
  knowledge {
    domain("programming") {
      ocaml: expert;
      rust: advanced;
      typescript: intermediate;
    }
    
    domain("design") {
      ui_ux: intermediate;
      "programming" connects_to "design" with 0.7;
    }
  }
  
  behaviors {
    when creativity > 0.8 -> seek("innovative solutions");
    when tired() -> avoid("complex debugging");
    when analytical > 0.7 -> prefer("systematic approach");
  }
  
  evolution {
    if learns("new language") then trait("curiosity") += 0.1;
    if interactions(50) then unlock_domain("philosophy");
    if learns("design pattern") then add_connection("programming", "design", 0.9);
  }
}
```

## Architecture

```
lib/
├── types.ml       # Core type definitions
├── lexer.mll      # Lexical analysis
├── parser.mly     # Grammar parsing (Menhir)
├── ast.ml         # Abstract Syntax Tree utilities
├── semantic.ml    # Semantic analysis & validation
├── compiler.ml    # Multi-target compilation
└── optimize.ml    # Personality optimization
```

## Compilation Targets

The DSL compiles to multiple formats:

- **JSON** - Structured data interchange
- **Lua** - Runtime personality scripts  
- **Prompt** - LLM system prompts
- **SQL** - Database storage schema
- **Cypher** - Neo4j graph database

```bash
# Compile personality to JSON
dsl-parser --input personality.colo --output json

# Compile to Lua runtime
dsl-parser --input personality.colo --output lua
```

## Features

### Trait Modifiers
- `decay(rate/time_unit)` - Natural strength reduction
- `when(context)` - Contextual activation
- `unless(context)` - Contextual suppression
- `amplifies(trait, factor)` - Cross-trait amplification
- `transforms_to(trait, factor, count)` - Trait evolution

### Knowledge System
- **Expertise levels**: beginner, intermediate, advanced, expert
- **Domain connections** with strength weights
- **Evolution rates** for knowledge transfer

### Behavioral Rules  
- **Conditions**: trait thresholds, context matches, state checks
- **Actions**: preferences, seeking behaviors, avoidance patterns

### Evolution Engine
- **Triggers**: learning events, interaction counts, time thresholds
- **Effects**: trait adjustments, domain unlocks, connection additions

## Semantic Analysis

Built-in validation detects:
- Circular dependencies in knowledge domains
- Conflicting trait modifiers  
- Non-deterministic evolution rules
- Unreachable behaviors
- Invalid domain references
- Unsafe trait modifications

## Docker Support

```bash
# Build container
docker build -f infrastructure/Dockerfile -t callosum-dsl .

# Run parser service
docker run -p 8001:8001 callosum-dsl
```

## Development

### Project Structure
```
├── bin/           # Executable entry point
├── lib/           # Core library modules
├── test/          # Comprehensive test suite
├── infrastructure/ # Docker deployment
└── *.colo         # Sample personality files
```

### Testing
```bash
# Run all tests
dune runtest

# Run specific test category  
dune exec test/test_parser.exe
```

### Adding New Features

1. **Extend types** in `types.ml`
2. **Update lexer** in `lexer.mll` for new tokens
3. **Modify grammar** in `parser.mly` for syntax
4. **Add validation** in `semantic.ml` 
5. **Update compiler** in `compiler.ml` for new targets
6. **Write tests** in `test/test_parser.ml`

## API Reference

### Core Functions
```ocaml
(* Parse personality from string *)
val parse_personality_from_string : ?filename:string -> string -> 
  (personality, parse_error list) result

(* Compile to target format *)  
val compile : personality -> target -> ?context:string -> unit ->
  (string, compiler_error list) result

(* Semantic analysis *)
val analyze : personality -> analysis_result

(* Optimization *)
val optimize_personality : personality -> level -> 
  personality * stats
```

## File Extensions

- `.colo` - Personality definition files
- `.colo.json` - Compiled JSON output
- `.colo.lua` - Compiled Lua scripts

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`dune runtest`)
5. Submit pull request

---

*Part of the Callosum AI Personality System*
