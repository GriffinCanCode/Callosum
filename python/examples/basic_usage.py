#!/usr/bin/env python3
"""
Basic usage example for Callosum Personality DSL with Provider-Agnostic AI Integration
"""

import sys
import os
# Add parent directory to path to import local callosum_dsl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import Callosum, PersonalityAI, PERSONALITY_TEMPLATES


def main():
    print("🎯 Callosum DSL - Provider-Agnostic Usage Example")
    print("=" * 50)
    
    # Create a compiler instance
    callosum = Callosum()
    
    # Example 1: Use a ready-made template
    print("\n1️⃣ Using a Ready-Made Template")
    dsl = PERSONALITY_TEMPLATES["helpful_assistant"]
    personality = callosum.to_json(dsl)
    
    print(f"Name: {personality['name']}")
    print(f"Traits: {len(personality['traits'])}")
    for trait in personality['traits']:
        print(f"  • {trait['name']}: {trait['strength']:.2f}")
    
    # Example 2: Create a custom personality
    print("\n2️⃣ Creating a Custom Personality")
    custom_dsl = '''personality: "Python Expert"

traits:
  technical_knowledge: 0.95
  helpfulness: 0.90
  patience: 0.85
  creativity: 0.75
  
knowledge:
  domain python:
    language_features: expert
    libraries: advanced
    debugging: expert
    
  domain teaching:
    explanation: advanced
    mentoring: intermediate
  
behaviors:
  - when technical_knowledge > 0.9 → prefer "code_examples"
  - when helpfulness > 0.8 → seek "complete_solutions"
  
evolution:
  - learns "user_style" → patience += 0.05'''
    
    custom_personality = callosum.to_json(custom_dsl)
    print(f"Created: {custom_personality['name']}")
    print(f"Knowledge domains: {[d['name'] for d in custom_personality['knowledge']]}")
    
    # Example 3: Generate system prompt for AI
    print("\n3️⃣ Generating System Prompt")
    system_prompt = callosum.to_prompt(custom_dsl)
    print("System prompt preview:")
    print(system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt)
    
    # Example 4: All compilation targets
    print("\n4️⃣ All Compilation Targets")
    formats = ["json", "prompt", "lua", "sql", "cypher"]
    
    for fmt in formats:
        output = callosum.compile(custom_dsl, fmt)
        print(f"✅ {fmt.upper()}: {len(output)} characters")
    
    # Example 5: Provider Detection and Setup
    print("\n5️⃣ Provider-Agnostic AI Integration")
    
    # Create PersonalityAI instance without provider (auto-detects)
    ai = PersonalityAI(custom_dsl)
    
    # Show available providers
    available_providers = ai.get_available_providers()
    print(f"Available providers: {available_providers}")
    
    # Show provider info
    provider_info = ai.get_provider_info()
    print(f"Current provider: {provider_info}")
    
    # Example 6: Multiple Provider Examples (commented out)
    print("\n6️⃣ Multi-Provider Examples (commented out)")
    print("""
# OpenAI Provider:
# ai.set_provider("openai", api_key="your-openai-key")
# response = ai.chat("Explain Python decorators")

# Anthropic Provider:
# ai.set_provider("anthropic", api_key="your-anthropic-key")
# response = ai.chat("Explain Python decorators")

# LangChain Provider (with any LangChain LLM):
# from langchain_openai import ChatOpenAI
# langchain_llm = ChatOpenAI(api_key="your-key", model="gpt-4")
# ai.set_provider("langchain", llm=langchain_llm)
# response = ai.chat("Explain Python decorators")

# Custom Provider:
# def my_chat_function(messages, model, **kwargs):
#     # Your custom AI logic here
#     return "Custom AI response"
# 
# ai.set_provider("generic", 
#                 chat_function=my_chat_function, 
#                 model_name="my-model",
#                 provider_name="my-ai-system")
""")
    
    # Example 7: LangChain Integration Examples
    print("\n7️⃣ LangChain Integration Examples")
    print("""
# Works with ANY LangChain LLM:

# OpenAI via LangChain:
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(api_key="key", model="gpt-4")
# ai = PersonalityAI(custom_dsl, provider="langchain", llm=llm)

# Anthropic via LangChain:
# from langchain_anthropic import ChatAnthropic
# llm = ChatAnthropic(api_key="key", model="claude-3-sonnet-20240229")
# ai = PersonalityAI(custom_dsl, provider="langchain", llm=llm)

# Local models via LangChain:
# from langchain_community.llms import Ollama
# llm = Ollama(model="llama2")
# ai = PersonalityAI(custom_dsl, provider="langchain", llm=llm)

# Any other LangChain-compatible model:
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_huggingface import HuggingFaceEndpoint
# llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key="key")
# ai = PersonalityAI(custom_dsl, provider="langchain", llm=llm)
""")
    
    # Example 8: Advanced Usage
    print("\n8️⃣ Advanced Usage Examples")
    print("""
# Conversation with history:
# response = ai.chat("Hello!", use_history=True)
# response = ai.chat("What was my first message?", use_history=True)

# Get personality insights:
# summary = ai.get_personality_summary()
# print(f"Dominant trait: {summary['dominant_trait']}")
# print(f"Provider: {summary['provider']}")

# Dynamic provider switching:
# ai.set_provider("openai", api_key="openai-key")
# openai_response = ai.chat("Hello from OpenAI")
# 
# ai.set_provider("anthropic", api_key="anthropic-key") 
# anthropic_response = ai.chat("Hello from Anthropic")
""")
    
    print("\n🎉 Provider-agnostic example complete!")
    print("\n💡 Key Benefits:")
    print("   • Switch between AI providers easily")
    print("   • Use any LangChain-compatible model")
    print("   • Create custom AI integrations")
    print("   • Same personality across all providers")
    print("   • Auto-detection of available providers")


def langchain_examples():
    """Extended examples showing LangChain integration patterns"""
    print("\n" + "="*60)
    print("🔗 EXTENDED LANGCHAIN EXAMPLES")
    print("="*60)
    
    custom_dsl = PERSONALITY_TEMPLATES["technical_mentor"]
    
    print("""
# Example: Multiple LangChain Models with Same Personality

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES

# Use the same personality across different models
personality = PERSONALITY_TEMPLATES["technical_mentor"]

# Method 1: Direct LangChain integration
try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    
    # OpenAI model
    openai_llm = ChatOpenAI(model="gpt-4", api_key="your-key")
    ai_openai = PersonalityAI(personality, provider="langchain", llm=openai_llm)
    
    # Anthropic model  
    claude_llm = ChatAnthropic(model="claude-3-sonnet-20240229", api_key="your-key")
    ai_claude = PersonalityAI(personality, provider="langchain", llm=claude_llm)
    
    # Same question to both models with same personality
    question = "How should I structure a large Python project?"
    
    openai_answer = ai_openai.chat(question)
    claude_answer = ai_claude.chat(question)
    
    # Both will have the same personality traits but different model responses
    
except ImportError:
    print("LangChain packages not installed")

# Method 2: Provider switching with same PersonalityAI instance
ai = PersonalityAI(personality)

# Switch to OpenAI
ai.set_provider("openai", api_key="your-openai-key")
openai_response = ai.chat("Explain design patterns")

# Switch to LangChain + Local model
try:
    from langchain_community.llms import Ollama
    local_llm = Ollama(model="codellama")
    ai.set_provider("langchain", llm=local_llm)
    local_response = ai.chat("Explain design patterns")
except ImportError:
    print("Local model not available")

# Method 3: Custom LangChain chains
try:
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    
    # Create a custom chain with personality-aware prompts
    personality_ai = PersonalityAI(personality)
    system_prompt = personality_ai.system_prompt
    
    # Use the compiled personality prompt in LangChain
    template = f\"\"\"{system_prompt}
    
Human: {{human_input}}
Assistant: \"\"\"
    
    prompt = PromptTemplate(template=template, input_variables=["human_input"])
    # Use with any LangChain LLM
    
except ImportError:
    print("LangChain chains not available")
""")


if __name__ == "__main__":
    main()
    
    # Uncomment to see extended LangChain examples
    # langchain_examples()
