# Callosum Backend - Personality System Architecture

The backend is organized around the core functions of the **Callosum Personality System**:

## Architecture Overview

```
backend/
├── personality/        # Core personality definition & management
├── intelligence/       # AI model integration & execution
├── knowledge/         # Knowledge graph & domain management  
├── evolution/         # Learning, adaptation & behavioral evolution
└── runtime/           # System orchestration & APIs
```

## Components

### 🧠 Personality (`personality/`)
The core of the system - defines, validates, and manages AI personalities through a custom DSL.

- **`dsl-parser/`** (OCaml) - Personality DSL parser, compiler, and type system
- **`validator/`** - Personality validation and semantic analysis
- **`templates/`** - Base personality templates and examples

### 🤖 Intelligence (`intelligence/`)  
AI model integration and personality-driven response generation.

- **`engine/`** (Python) - AI model management, prompt compilation, and execution
- **`models/`** - Model adapters, LoRA management, and fine-tuning
- **`prompts/`** - Prompt templates and personality-aware compilation

### 📚 Knowledge (`knowledge/`)
Knowledge representation, graph management, and domain expertise modeling.

- **`graph/`** (Go) - High-performance graph operations and algorithms
- **`domains/`** - Knowledge domain definitions and management
- **`connections/`** - Inter-domain relationships and learning pathways

### 🧬 Evolution (`evolution/`)
Real-time learning, behavioral adaptation, and personality evolution.

- **`processor/`** (Elixir/OTP) - Event streaming, pattern recognition, and real-time processing
- **`patterns/`** - Behavioral pattern mining and analysis
- **`adaptation/`** - Personality adaptation and evolution logic

### ⚙️ Runtime (`runtime/`)
System orchestration, service coordination, and API management.

- **`orchestrator/`** - Main system coordinator and service management
- **`apis/`** - REST/GraphQL APIs for each subsystem
- **`gateway/`** - API gateway and service mesh

## Technology Stack

- **OCaml**: DSL parsing, compilation, and type safety
- **Python**: AI/ML integration, model management  
- **Go**: High-performance graph operations
- **Elixir/OTP**: Concurrent event processing and supervision
- **Rust** (planned): System orchestration and Tauri integration

## Data Flow

1. **Personality Definition** → DSL parsed and validated
2. **Intelligence Integration** → Personality compiled to prompts and model configs
3. **Knowledge Management** → Domains and connections managed in graph
4. **Evolution Processing** → Real-time behavioral learning and adaptation
5. **Runtime Coordination** → All components orchestrated through unified APIs

This architecture ensures each component has a clear responsibility while enabling seamless data flow through the personality system lifecycle.
