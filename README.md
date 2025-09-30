# Callosum Personality DSL Compiler

[![PyPI version](https://badge.fury.io/py/callosum-dsl.svg)](https://badge.fury.io/py/callosum-dsl)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A provider-agnostic DSL compiler for creating AI personalities that produce genuinely different behaviors.** Write personalities in a clean, readable domain-specific language that compiles to comprehensive system prompts, creating measurably distinct AI responses across **any AI provider** - OpenAI, Anthropic, **any LangChain model**, or custom systems.

**Works with ANY AI provider:**
- **LangChain** - Use any LangChain-compatible model (OpenAI, Anthropic, local models, etc.)
- **OpenAI** - Direct integration with GPT models
- **Anthropic** - Direct integration with Claude models  
- **Custom AI systems** - Integrate with any AI via simple function wrapper

## What is Callosum?

**Callosum creates genuinely different AI personalities** that produce measurably distinct behaviors across any AI provider. Unlike simple prompt templates, Callosum compiles rich personality definitions into comprehensive system prompts that actually change how AI models respond.

Callosum compiles `.colo` personality files into formats you can use with AI systems:

```python
from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES

# Use pre-built personality with auto-detected AI provider
ai = PersonalityAI(PERSONALITY_TEMPLATES["helpful_assistant"])

# Works with any provider - just switch as needed!
ai.set_provider("openai", api_key="your-key")
response = ai.chat("Help me code")

# Switch to LangChain (works with ANY LangChain model)
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", api_key="your-key") 
ai.set_provider("langchain", llm=llm)
response = ai.chat("Same personality, different model!")
```

**Or just compile personalities for your own systems:**

```python
from callosum_dsl import Callosum

callosum = Callosum()
system_prompt = callosum.to_prompt(personality_dsl)  # For any LLM API
personality_config = callosum.to_json(personality_dsl)  # Structured data
```

## Quick Start

### Installation

```bash
pip install callosum-dsl
```

*Note: AI provider packages (like `openai`, `anthropic`, `langchain-*`) are optional and installed separately as needed.*

### Provider-Agnostic AI Usage

```python
from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES

# Create AI with personality (auto-detects available providers)
ai = PersonalityAI(PERSONALITY_TEMPLATES["technical_mentor"])

# Option 1: Use with OpenAI
ai.set_provider("openai", api_key="your-openai-key")
response = ai.chat("Explain Python decorators")

# Option 2: Use with Anthropic  
ai.set_provider("anthropic", api_key="your-anthropic-key")
response = ai.chat("Explain Python decorators")

# Option 3: Use with ANY LangChain model
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.llms import Ollama  # Local models!

# OpenAI via LangChain
llm = ChatOpenAI(model="gpt-4", api_key="your-key")
ai.set_provider("langchain", llm=llm)

# Anthropic via LangChain  
llm = ChatAnthropic(model="claude-3-sonnet-20240229", api_key="your-key")
ai.set_provider("langchain", llm=llm)

# Local model via LangChain
llm = Ollama(model="llama2")
ai.set_provider("langchain", llm=llm)

# Same personality, different models!
response = ai.chat("Explain Python decorators")
```

### Basic Compilation

```python
from callosum_dsl import Callosum, PERSONALITY_TEMPLATES

# Initialize the compiler
callosum = Callosum()

# Use a ready-made personality
personality_dsl = PERSONALITY_TEMPLATES["helpful_assistant"]

# Compile to different formats
personality_data = callosum.to_json(personality_dsl)
system_prompt = callosum.to_prompt(personality_dsl)

print(f"Created: {personality_data['name']}")
print(f"Traits: {len(personality_data['traits'])}")
```

### Create Custom Personalities

```python
# Define a custom AI personality
custom_personality = '''
personality: "Python Expert Assistant"

traits:
  technical_expertise: 0.95
  helpfulness: 0.90
    amplifies: teaching * 1.3
  patience: 0.85
    when: "explaining_concepts"
  creativity: 0.75

knowledge:
  domain programming:
    python: expert
    debugging: expert
    best_practices: advanced
    frameworks: advanced
    
  domain teaching:
    code_explanation: expert
    mentoring: advanced
    connects_to: programming (0.9)

behaviors:
  - when technical_expertise > 0.9 → prefer "detailed code examples"
  - when helpfulness > 0.8 → seek "comprehensive solutions"
  - when patience > 0.8 → avoid "overwhelming complexity"

evolution:
  - learns "user_coding_style" → patience += 0.05
  - learns "effective_teaching" → helpfulness += 0.1
'''

# Compile the personality
personality = callosum.to_json(custom_personality)
system_prompt = callosum.to_prompt(custom_personality)
```

## How Callosum Actually Works

### Personalities Create Real Behavioral Differences

Callosum doesn't just change labels - it creates **measurably different AI behaviors**. Here's what the same question produces across different personalities:

**Question:** *"How should I approach learning something new?"*

**🎭 Helpful Assistant (helpfulness: 0.95, empathy: 0.85):**
> "Learning something new can be an exciting yet challenging endeavor. Here are some steps you might consider: 1. Set Clear Goals... 2. Break it Down: Large tasks can seem daunting..."

*Response style: Structured, supportive, acknowledges user challenges*

**🎨 Creative Writer (creativity: 0.95, imagination: 0.90):**
> "Ah, the thrill of embarking on a new learning journey! It's akin to stepping into a new world, filled with unexplored territories and hidden treasures... inspired by the art of storytelling."

*Response style: Metaphorical, poetic language, storytelling approach*

**👨‍💻 Technical Mentor (technical_expertise: 0.95, precision: 0.88):**
> "Learning something new, especially in the field of programming, can be a challenging yet rewarding experience. Here's a systematic approach that you can follow..."

*Response style: Domain-focused, methodical, technical precision*

### Trait Values Matter

Small changes in trait values produce **measurably different behaviors**:

**Low Helpfulness (0.3):** *"I might not be able to solve everything for you"* - hesitant, self-limiting
**High Helpfulness (0.95):** *"I'm here to help you with the most effective assistance"* - confident, proactive

**Low Creativity (0.2):** *"A rainy day is characterized by continuous fall of water droplets from the sky..."* - factual, scientific
**High Creativity (0.95):** *"A symphony of droplets descends from the heavens, each one a tiny messenger..."* - poetic, metaphorical

### Cross-Provider Consistency

The same personality maintains its characteristics across **any AI provider**:

```python
# Same personality, different providers - consistent behavior
personality = PERSONALITY_TEMPLATES["technical_mentor"]

# OpenAI: Systematic, programming-focused explanations
ai.set_provider("openai", api_key="key")

# Anthropic: Same systematic, programming-focused style  
ai.set_provider("anthropic", api_key="key")

# LangChain + any model: Maintains technical mentor traits
ai.set_provider("langchain", llm=any_langchain_model)
```

### What You Get vs. Generic Prompts

**❌ Generic Prompt:** *"You are a helpful AI assistant"*
- Produces standard, predictable responses
- No personality consistency across interactions
- Generic tone regardless of context

**✅ Callosum Personality:** Compiles to 1,000+ character system prompts including:
- Detailed trait specifications with numerical values
- Knowledge domain expertise mappings  
- Behavioral rules and contextual preferences
- Evolution patterns for learning and adaptation

```
# AI Personality Profile: Technical Programming Mentor

## Core Traits
Technical_expertise: Very high strength (0.95/1.0)
Teaching_ability: Very high strength (0.90/1.0)
Precision: Very high strength (0.88/1.0)
Patience: High strength (0.85/1.0)

## Knowledge Domains
Programming: Expert level proficiency
- Software architecture: Expert
- Debugging: Expert  
- Code review: Advanced
- Best practices: Expert

## Behavioral Guidelines
When technical_expertise > 0.9: Prefer detailed explanations
When teaching_ability > 0.8: Seek teaching opportunities
...
```

## AI Provider Integration

### LangChain Integration (Recommended)
```python
from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES

# Works with ANY LangChain model!
personality = PERSONALITY_TEMPLATES["creative_writer"]

# Google Gemini (example - requires langchain-google-genai)
# from langchain_google_genai import ChatGoogleGenerativeAI
# llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key="key")
# ai = PersonalityAI(personality, provider="langchain", llm=llm)

# Local Ollama models (example - requires langchain-community)
# from langchain_community.llms import Ollama
# llm = Ollama(model="codellama")
# ai = PersonalityAI(personality, provider="langchain", llm=llm)

# Most common: OpenAI via LangChain
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", api_key="your-key")
ai = PersonalityAI(personality, provider="langchain", llm=llm)

# Same personality across all models
response = ai.chat("Write a creative story")
```

### Direct Provider Integration
```python
from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES

ai = PersonalityAI(PERSONALITY_TEMPLATES["technical_mentor"])

# OpenAI
ai.set_provider("openai", api_key="your-key")
response = ai.chat("Explain design patterns")

# Anthropic
ai.set_provider("anthropic", api_key="your-key") 
response = ai.chat("Explain design patterns")

# Conversation history works with all providers
response1 = ai.chat("Hello, I'm learning Python", use_history=True)
response2 = ai.chat("What did I say I was learning?", use_history=True)
```

### Custom AI Integration
```python
# Integrate with your own AI system
def my_ai_function(messages, model, **kwargs):
    # Your custom AI logic here
    user_msg = messages[-1]["content"]
    return f"Custom AI response to: {user_msg}"

ai = PersonalityAI(
    personality_dsl,
    provider="generic",
    chat_function=my_ai_function,
    model_name="my-custom-model"
)

response = ai.chat("Hello!")  # Uses your custom AI with personality
```

### Traditional Compilation Approach
```python
# For manual integration with any system
from callosum_dsl import Callosum

callosum = Callosum()
system_prompt = callosum.to_prompt(personality_dsl)

# Use with any LLM API manually
import openai
client = openai.OpenAI(api_key="your-key")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Help me code"}
    ]
)

# Or get structured data for your own system
personality_data = callosum.to_json(personality_dsl)
sql_schema = callosum.to_sql(personality_dsl) 
```

## What Callosum Does

**Callosum is a personality definition compiler that creates behaviorally distinct AI personalities** - it takes structured personality descriptions and compiles them into comprehensive system prompts (1,000+ characters) that produce measurably different AI behaviors across any AI system.

### **Compilation Targets**
```python
# System prompts for LLM APIs
prompt = callosum.to_prompt(personality_dsl)

# Structured JSON for custom frameworks  
data = callosum.to_json(personality_dsl)

# Lua scripts for dynamic systems
script = callosum.to_lua(personality_dsl)

# Database schemas for persistence
sql = callosum.to_sql(personality_dsl)

# Graph queries for relationship modeling
cypher = callosum.to_cypher(personality_dsl)
```

### **Personality Features**
- **Trait System** - Numeric values with modifiers (decay, amplification, context)
- **Knowledge Domains** - Structured expertise areas with connections
- **Behavioral Rules** - Context-aware response preferences
- **Evolution Patterns** - How personalities change through interactions

### **Output Formats**
- **System Prompts** - Use with OpenAI, Anthropic, Claude, any LLM
- **JSON Config** - Feed into custom AI frameworks and applications  
- **Lua Scripts** - Runtime personality systems
- **SQL/Cypher** - Database storage for persistent personalities

## Key Benefits

### **Provider Agnostic**
- **Switch AI providers instantly** without changing your personality definitions
- **Future-proof** - works with new AI models as they emerge
- **No vendor lock-in** - your personalities work everywhere

### **LangChain Integration**
- Works with **LangChain-compatible models**:
  - OpenAI, Anthropic models via LangChain
  - Local models (Ollama integration)
  - HuggingFace endpoints
  - Custom LangChain implementations

### **Verified Behavioral Differences**
- **Measurably different AI responses** - personalities create 200-400+ character response variations
- **Trait-specific behaviors** - creativity: 0.2 vs 0.95 produces factual vs poetic language
- **Cross-provider consistency** - same personality maintains characteristics on OpenAI, Anthropic, LangChain
- **Precision matters** - small trait changes (0.3 → 0.95) create distinct behavioral shifts
- Rich personality features (traits, knowledge domains, behaviors, evolution)

### **Developer Friendly**
- Simple API - change providers with one line of code
- Auto-detection of available providers
- Comprehensive examples and documentation
- Backwards compatible with existing code

## **DSL Language Reference**

### Trait Modifiers
```python
# Traits that change over time
patience: 0.8
  decays: 0.02/month

# Context-dependent activation  
creativity: 0.9
  when: "creative_tasks"

# Conditional suppression
formality: 0.6
  unless: "user_frustrated"

# Cross-trait interactions
curiosity: 0.8
  amplifies: helpfulness * 1.4
```

### Knowledge Domains
```python
domain programming:
  python: expert           # Expertise levels
  debugging: advanced      # beginner | intermediate | advanced | expert
  frameworks: intermediate

# Domain connections
domain teaching:
  connects_to: programming (0.9)
```

### Behavioral Rules
```python
behaviors:
  - when technical_expertise > 0.9 → prefer "detailed examples"
  - when "user_confused" → avoid "complex jargon"
  - when patience > 0.8 → seek "step-by-step guidance"
```

### Evolution & Learning
```python
evolution:
  - learns "user_preference" → helpfulness += 0.05
  - after 100.0 interactions → unlock "advanced_topics"
  - learns "effective_method" → connect domain1 ↔ domain2 (0.9)
```

## **Ready-Made Personalities**

```python
from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES

# Available templates
print(list(PERSONALITY_TEMPLATES.keys()))
# ['helpful_assistant', 'creative_writer', 'technical_mentor']

# Use directly with any AI provider
ai = PersonalityAI(PERSONALITY_TEMPLATES["creative_writer"])

# Works instantly with any provider:
ai.set_provider("openai", api_key="your-key")
story = ai.chat("Write a story about AI")

# Or use with LangChain models
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", api_key="your-key")
ai.set_provider("langchain", llm=llm)
poem = ai.chat("Write a poem about coding")

# Traditional compilation still works
from callosum_dsl import Callosum
callosum = Callosum()
writer_prompt = callosum.to_prompt(PERSONALITY_TEMPLATES["creative_writer"])
```

## Development

### Project Structure
```
callosum/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT license
├── Makefile                     # Development commands
│
├── core/                        # OCaml DSL Compiler
│   ├── bin/                     # Executable entry point
│   │   └── main.ml              # Command-line interface
│   ├── lib/                     # Core library modules
│   │   ├── ast.ml               # Abstract Syntax Tree
│   │   ├── compiler.ml          # Multi-target compilation
│   │   ├── lexer.mll            # Lexical analysis
│   │   ├── parser.mly           # Grammar parsing
│   │   ├── semantic.ml          # Semantic analysis
│   │   ├── types.ml             # Type definitions
│   │   └── optimize.ml          # Optimization passes
│   ├── test/                    # Comprehensive test suite
│   ├── examples/                # Sample .colo personality files
│   ├── infrastructure/          # Docker deployment
│   ├── dune-project             # OCaml build configuration
│   └── dsl-parser.opam          # Package definition
│
├── python/                      # Python Package
│   ├── callosum_dsl/           # Python package source
│   ├── tests/                   # Python tests
│   ├── examples/                # Python usage examples
│   ├── pyproject.toml           # Modern Python build config
│   └── requirements.txt         # Python dependencies
│
├── docs/                        # Documentation
│   ├── README_PYTHON.md         # Python package documentation
│   ├── QUICK_START.md           # Quick start guide
│   ├── PACKAGING.md             # Package maintenance docs
│   └── READY_FOR_PYPI.md        # PyPI publishing guide
│
└── scripts/                     # Build and utility scripts
    ├── build_package.py         # Automated build script
    └── publish.py               # Publishing script
```

### Development

```bash
# Quick development setup
make dev

# Build OCaml compiler
make build-core

# Build Python package  
make build-python

# Run tests
make test

# Clean builds
make clean
```

For detailed OCaml development:
```bash
cd core
dune build              # Build
dune runtest            # Run tests
dune exec bin/main.exe  # Run compiler directly
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
```python
# Python API
from callosum_dsl import Callosum, PersonalityAI

# Compile DSL to different formats
callosum = Callosum()
system_prompt = callosum.to_prompt(dsl_content)
data = callosum.to_json(dsl_content)
lua_script = callosum.to_lua(dsl_content)

# Provider-agnostic AI usage
ai = PersonalityAI(dsl_content)
ai.set_provider("openai", api_key="your-key")
response = ai.chat("Hello!")
```

## File Extensions

- `.colo` - Personality definition files (Callosum language)
- Output formats: JSON, system prompts, Lua, SQL, Cypher

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
