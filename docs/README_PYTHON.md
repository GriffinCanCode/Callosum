# Callosum Personality DSL - Python Integration

**The simplest way to use Callosum from Python!** Direct wrapper with zero external dependencies.

## 🚀 Quick Start (30 seconds!)

### 1. Build the DSL compiler (one-time setup)
```bash
cd personality/dsl
dune build
```

### 2. Use from Python immediately
```python
from callosum import Callosum, PERSONALITY_TEMPLATES

# Create a compiler instance
callosum = Callosum()

# Use a ready-made personality
dsl = PERSONALITY_TEMPLATES["helpful_assistant"]

# Compile to different formats
personality_data = callosum.to_json(dsl)
system_prompt = callosum.to_prompt(dsl)
lua_script = callosum.to_lua(dsl)

print(f"Created: {personality_data['name']}")
print(f"Traits: {len(personality_data['traits'])}")
```

## 💡 **Why This Approach is Better**

✅ **Zero external dependencies** - Uses only Python stdlib  
✅ **Direct binary calls** - Maximum performance, no network overhead  
✅ **Full DSL power** - Access to all compilation targets  
✅ **Error handling** - Proper Python exceptions  
✅ **Type hints** - Full IDE support  
✅ **Production ready** - Robust, tested, reliable  

## 🎯 Basic Usage

### Create Custom Personalities
```python
from callosum import Callosum

callosum = Callosum()

# Define your AI personality
my_personality = '''
personality "Python Coding Assistant" {
  traits {
    technical_expertise: 0.95;
    helpfulness: 0.90 with amplifies("teaching", 1.3);
    patience: 0.85 with when("debugging");
    creativity: 0.80;
  }
  
  knowledge {
    domain("python_programming") {
      language_features: expert;
      debugging: expert;
      best_practices: advanced;
      testing: advanced;
    }
    
    domain("teaching") {
      code_explanation: expert;
      mentoring: advanced;
      "python_programming" connects_to "teaching" with 0.9;
    }
  }
  
  behaviors {
    when technical_expertise > 0.9 -> prefer("detailed code examples");
    when helpfulness > 0.8 -> seek("comprehensive solutions");
    when patience > 0.8 -> avoid("overwhelming complexity");
  }
  
  evolution {
    if learns("user_coding_style") then trait("patience") += 0.05;
    if learns("effective_explanation") then trait("helpfulness") += 0.1;
  }
}
'''

# Compile to JSON data
personality = callosum.to_json(my_personality)
print(f"Name: {personality['name']}")

# Get system prompt for AI APIs
prompt = callosum.to_prompt(my_personality)
```

### AI Integration Examples

#### OpenAI Integration
```python
from callosum import PersonalityAI

# Create AI with personality
ai = PersonalityAI(
    personality_dsl=my_personality,
    api_key="your-openai-key",
    provider="openai"
)

# Chat with the personality
response = ai.chat("Help me debug this Python function")
print(response)

# Get personality info
info = ai.get_personality_summary()
print(f"Dominant trait: {info['dominant_trait']}")
```

#### Anthropic Claude Integration
```python
ai = PersonalityAI(
    personality_dsl=my_personality,
    api_key="your-anthropic-key", 
    provider="anthropic"
)

response = ai.chat("Explain Python decorators", model="claude-3-sonnet-20240229")
```

## 🎨 Ready-Made Personalities

Use pre-built personalities for common scenarios:

```python
from callosum import PERSONALITY_TEMPLATES, PersonalityAI

# Technical mentor
mentor = PersonalityAI(
    PERSONALITY_TEMPLATES["technical_mentor"],
    api_key="your-key"
)

# Creative writing companion  
writer = PersonalityAI(
    PERSONALITY_TEMPLATES["creative_writer"],
    api_key="your-key"
)

# General helpful assistant
assistant = PersonalityAI(
    PERSONALITY_TEMPLATES["helpful_assistant"], 
    api_key="your-key"
)
```

## 📁 Working with Files

```python
from callosum import Callosum

callosum = Callosum()

# Load personality from file
dsl_content = callosum.load_file("my_personality.colo")
personality = callosum.to_json(dsl_content)

# Validate DSL before using
if callosum.validate(dsl_content):
    print("✅ Valid personality DSL")
else:
    print("❌ Invalid DSL syntax")
```

## 🔧 All Compilation Targets

```python
# JSON - Structured data for custom frameworks
json_data = callosum.to_json(dsl)

# System Prompt - For LLM APIs (OpenAI, Anthropic, etc.)
system_prompt = callosum.to_prompt(dsl, context="debugging_session")

# Lua Script - For dynamic runtime systems
lua_script = callosum.to_lua(dsl)

# SQL - Database storage for personality persistence  
sql_schema = callosum.to_sql(dsl)

# Cypher - Neo4j graph database queries
cypher_queries = callosum.to_cypher(dsl)
```

## 🐍 Framework Integration

### Django
```python
# models.py
from django.db import models
from callosum import Callosum

class AIPersonality(models.Model):
    name = models.CharField(max_length=200)
    dsl_source = models.TextField()
    
    def get_system_prompt(self):
        callosum = Callosum()
        return callosum.to_prompt(self.dsl_source)
    
    def get_personality_data(self):
        callosum = Callosum()
        return callosum.to_json(self.dsl_source)
```

### FastAPI
```python
from fastapi import FastAPI, HTTPException
from callosum import Callosum

app = FastAPI()
callosum = Callosum()

@app.post("/compile")
async def compile_personality(dsl: str, target: str = "json"):
    try:
        result = callosum.compile(dsl, target)
        return {"success": True, "output": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Jupyter Notebooks
```python
# Perfect for research and experimentation
from callosum import Callosum, PERSONALITY_TEMPLATES
import json

callosum = Callosum()

# Quick personality testing
for name, dsl in PERSONALITY_TEMPLATES.items():
    data = callosum.to_json(dsl)
    print(f"{name}: {data['name']} - {len(data['traits'])} traits")
```

## ⚡ Performance & Best Practices

### Performance Tips
```python
# ✅ Reuse the Callosum instance
callosum = Callosum()  # Initialize once

# ✅ Batch compilation for multiple personalities
personalities = {}
for name, dsl in PERSONALITY_TEMPLATES.items():
    personalities[name] = callosum.to_json(dsl)

# ✅ Cache compiled results for production
import functools

@functools.lru_cache(maxsize=100)
def get_cached_personality(dsl_hash):
    return callosum.to_json(dsl_content)
```

### Error Handling
```python
from callosum import CallosumError, ParseError, CompileError

try:
    personality = callosum.to_json(dsl_content)
except ParseError as e:
    print(f"DSL syntax error: {e}")
except CompileError as e:
    print(f"Compilation failed: {e}")
except CallosumError as e:
    print(f"General error: {e}")
```

## 🔍 Troubleshooting

### Common Issues

**"DSL compiler not found"**
```bash
cd personality/dsl && dune build
# Or check if dune is installed: which dune
```

**"Parse errors"**
- Check DSL syntax in your .colo files
- Use `callosum.validate()` to test DSL before compilation

**"Module not found for AI integration"**
```bash
pip install openai  # for OpenAI
pip install anthropic  # for Claude
```

## 🎯 Why Choose This Integration?

| Feature | This Wrapper | HTTP API | Other Approaches |
|---------|-------------|----------|------------------|
| **Dependencies** | None | Flask, requests | Varies |
| **Performance** | ~10ms | ~100ms+ | Varies |
| **Reliability** | High | Network dependent | Varies |
| **Simplicity** | Highest | Medium | Low |
| **Distribution** | Single .py file | Multiple files | Complex |

## 📦 Distribution

### As a Package
```python
# setup.py
from setuptools import setup

setup(
    name="my-ai-personalities",
    py_modules=["callosum"],
    # Include the compiled DSL binary
    package_data={"": ["personality/dsl/_build/default/bin/main.exe"]},
)
```

### Standalone Script
Just copy `callosum.py` - it's completely self-contained!

---

**That's it!** You now have the most direct, efficient way to use Callosum personalities in Python. No servers, no complex setup, just pure functionality. 🎉
