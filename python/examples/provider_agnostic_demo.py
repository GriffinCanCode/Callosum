#!/usr/bin/env python3
"""
Demo script showing provider-agnostic AI integration with Callosum DSL
"""

import sys
import os
# Add parent directory to path to import local callosum_dsl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES, auto_detect_providers

def demo_provider_detection():
    """Demo automatic provider detection"""
    print("🔍 PROVIDER DETECTION DEMO")
    print("=" * 40)
    
    available = auto_detect_providers()
    print(f"Available AI providers: {available}")
    
    if not available:
        print("❌ No AI providers detected. Install one of:")
        print("   • pip install openai")
        print("   • pip install anthropic") 
        print("   • pip install langchain-core")
        return None
    
    return available

def demo_basic_usage():
    """Demo basic provider-agnostic usage"""
    print("\n🎯 BASIC USAGE DEMO")
    print("=" * 40)
    
    # Create AI with auto-detected provider
    personality_dsl = PERSONALITY_TEMPLATES["helpful_assistant"]
    ai = PersonalityAI(personality_dsl)
    
    # Show provider info
    info = ai.get_provider_info()
    print(f"Provider: {info['provider']}")
    print(f"Default model: {info['default_model']}")
    
    # Show personality summary
    summary = ai.get_personality_summary()
    print(f"\nPersonality: {summary['name']}")
    print(f"Dominant trait: {summary['dominant_trait']}")
    print(f"Traits: {list(summary['traits'].keys())}")
    
    return ai

def demo_langchain_integration():
    """Demo LangChain integration"""
    print("\n🔗 LANGCHAIN INTEGRATION DEMO")
    print("=" * 40)
    
    try:
        # Try to import LangChain
        from langchain_core.messages import HumanMessage, SystemMessage
        print("✅ LangChain core is available")
        
        # Create a mock LangChain LLM for demo
        class MockLangChainLLM:
            def __init__(self, model_name="mock-model"):
                self.model_name = model_name
            
            def invoke(self, messages, **kwargs):
                # Simple mock response
                return type('Response', (), {'content': f"Mock response from {self.model_name}"})()
        
        # Create AI with mock LangChain LLM
        mock_llm = MockLangChainLLM("demo-model")
        ai = PersonalityAI(
            PERSONALITY_TEMPLATES["technical_mentor"],
            provider="langchain",
            llm=mock_llm
        )
        
        print(f"✅ LangChain provider initialized")
        print(f"Provider: {ai.get_provider_info()['provider']}")
        
        # Test chat (will use mock)
        response = ai.chat("Hello!")
        print(f"Response: {response}")
        
        return ai
        
    except ImportError:
        print("❌ LangChain not available")
        print("Install with: pip install langchain-core")
        return None

def demo_custom_provider():
    """Demo custom provider integration"""
    print("\n🛠️ CUSTOM PROVIDER DEMO")
    print("=" * 40)
    
    def my_custom_ai_function(messages, model, **kwargs):
        """Custom AI function that processes messages"""
        # Extract the user message
        user_message = None
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        # Simple response logic
        if "hello" in user_message.lower():
            return "Hello! I'm a custom AI with personality!"
        elif "python" in user_message.lower():
            return "Python is great! Let me help you with that."
        else:
            return f"You said: '{user_message}'. I'm responding with my personality!"
    
    # Create AI with custom provider
    ai = PersonalityAI(
        PERSONALITY_TEMPLATES["creative_writer"],
        provider="generic",
        chat_function=my_custom_ai_function,
        model_name="custom-v1.0",
        provider_name="MyCustomAI"
    )
    
    print(f"✅ Custom provider initialized")
    provider_info = ai.get_provider_info()
    print(f"Provider: {provider_info['provider']}")
    print(f"Model: {provider_info['default_model']}")
    
    # Test custom AI
    test_messages = ["Hello!", "Help me with Python", "Tell me a story"]
    for msg in test_messages:
        response = ai.chat(msg)
        print(f"Q: {msg}")
        print(f"A: {response}\n")
    
    return ai

def demo_provider_switching():
    """Demo dynamic provider switching"""
    print("\n🔄 PROVIDER SWITCHING DEMO")
    print("=" * 40)
    
    # Start with one personality
    ai = PersonalityAI(PERSONALITY_TEMPLATES["helpful_assistant"])
    print(f"Initial provider: {ai.get_provider_info()['provider']}")
    
    # Create custom provider function
    def provider1(messages, model, **kwargs):
        return "Response from Provider 1"
    
    def provider2(messages, model, **kwargs):
        return "Response from Provider 2"
    
    # Switch between providers
    ai.set_provider("generic", 
                    chat_function=provider1, 
                    model_name="model-1",
                    provider_name="provider-1")
    
    response1 = ai.chat("Test message")
    print(f"Provider 1 response: {response1}")
    
    # Switch to different provider
    ai.set_provider("generic",
                    chat_function=provider2,
                    model_name="model-2", 
                    provider_name="provider-2")
    
    response2 = ai.chat("Test message")
    print(f"Provider 2 response: {response2}")
    
    # Show how personality stays the same
    summary = ai.get_personality_summary()
    print(f"\nPersonality remains: {summary['name']}")
    print(f"Current provider: {summary['provider']}")

def main():
    """Run all demos"""
    print("🚀 CALLOSUM PROVIDER-AGNOSTIC AI DEMO")
    print("=" * 50)
    
    # 1. Provider detection
    available_providers = demo_provider_detection()
    
    # 2. Basic usage  
    basic_ai = demo_basic_usage()
    
    # 3. LangChain integration
    langchain_ai = demo_langchain_integration()
    
    # 4. Custom provider
    custom_ai = demo_custom_provider()
    
    # 5. Provider switching
    demo_provider_switching()
    
    print("\n🎉 ALL DEMOS COMPLETE!")
    print("\n💡 Summary:")
    print("   • Callosum works with any AI provider")
    print("   • LangChain integration supports any LLM")
    print("   • Custom providers enable any AI system") 
    print("   • Same personality across all providers")
    print("   • Dynamic provider switching at runtime")

if __name__ == "__main__":
    main()
