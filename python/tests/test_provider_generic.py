#!/usr/bin/env python3
"""
Generic provider tests for Callosum DSL
Tests custom AI provider integrations and scenarios
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES, CallosumError, create_provider


class TestGenericProvider:
    """Test generic/custom provider functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_personality = PERSONALITY_TEMPLATES["helpful_assistant"]
        
    def test_generic_provider_creation(self):
        """Test generic provider creation"""
        def simple_chat(messages, model, **kwargs):
            return "Simple response"
        
        provider = create_provider(
            "generic", 
            chat_function=simple_chat,
            model_name="custom-v1.0",
            provider_name="SimpleAI"
        )
        
        assert provider.provider_name == "SimpleAI"
        assert provider.default_model == "custom-v1.0"
    
    def test_generic_provider_missing_function(self):
        """Test error when chat function is missing"""
        with pytest.raises(ValueError, match="chat_function must be callable"):
            create_provider("generic", chat_function=None)
    
    def test_generic_provider_invalid_function(self):
        """Test error when chat function is not callable"""
        with pytest.raises(ValueError, match="chat_function must be callable"):
            create_provider("generic", chat_function="not_callable")
    
    def test_generic_provider_chat(self):
        """Test generic provider chat functionality"""
        def custom_chat(messages, model, **kwargs):
            user_message = messages[-1]["content"] if messages else ""
            return f"Custom AI ({model}) responds to: {user_message}"
        
        provider = create_provider(
            "generic",
            chat_function=custom_chat,
            model_name="custom-model-v2",
            provider_name="CustomAI"
        )
        
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello AI"}
        ]
        
        response = provider.chat(messages, model="custom-model-v2")
        assert response == "Custom AI (custom-model-v2) responds to: Hello AI"
    
    def test_personality_ai_with_generic(self):
        """Test PersonalityAI with generic provider"""
        def ai_function(messages, model, **kwargs):
            # Extract system and user messages
            system_msg = ""
            user_msg = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                elif msg["role"] == "user":
                    user_msg = msg["content"]
            
            # Respond based on personality traits mentioned in system prompt
            if "helpfulness" in system_msg.lower():
                return f"I'm here to help! You said: {user_msg}"
            else:
                return f"Generic response to: {user_msg}"
        
        # Create PersonalityAI with generic provider
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=ai_function,
            model_name="helpful-ai-v1",
            provider_name="HelpfulAI"
        )
        
        # Test provider info
        provider_info = ai.get_provider_info()
        assert provider_info["provider"] == "HelpfulAI"
        assert provider_info["default_model"] == "helpful-ai-v1"
        assert provider_info["has_provider"] is True
        
        # Test chat (should use personality system prompt)
        response = ai.chat("I need help with coding")
        assert "I'm here to help!" in response
        assert "I need help with coding" in response
    
    def test_generic_stateful_ai(self):
        """Test generic provider with stateful AI implementation"""
        class StatefulAI:
            def __init__(self):
                self.memory = []
                self.interaction_count = 0
            
            def chat(self, messages, model, **kwargs):
                self.interaction_count += 1
                
                # Store user message
                for msg in messages:
                    if msg["role"] == "user":
                        self.memory.append(msg["content"])
                
                # Generate response based on memory
                if self.interaction_count == 1:
                    return "Hello! I'm learning about you."
                elif len(self.memory) > 1:
                    return f"I remember you mentioned: {', '.join(self.memory[:-1])}"
                else:
                    return "Let's continue our conversation."
        
        stateful_ai = StatefulAI()
        
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=stateful_ai.chat,
            model_name="stateful-v1",
            provider_name="StatefulAI"
        )
        
        # Test conversation with memory
        response1 = ai.chat("I like Python")
        assert response1 == "Hello! I'm learning about you."
        
        response2 = ai.chat("I also like JavaScript")
        assert "I like Python" in response2
    
    def test_generic_external_api_simulation(self):
        """Test generic provider simulating external API"""
        def external_api_chat(messages, model, **kwargs):
            """Simulate calling an external AI API"""
            
            # Simulate API request processing
            user_message = None
            system_prompt = None
            
            for msg in messages:
                if msg["role"] == "user":
                    user_message = msg["content"]
                elif msg["role"] == "system":
                    system_prompt = msg["content"]
            
            # Simulate API response based on parameters
            api_response = {
                "status": "success",
                "response": f"External API response to '{user_message}'",
                "model_used": model,
                "temperature": kwargs.get("temperature", 0.5),
                "personality_detected": "helpful" in system_prompt.lower() if system_prompt else False
            }
            
            # Return formatted response
            personality_note = " (with helpful personality)" if api_response["personality_detected"] else ""
            return f"{api_response['response']} using {api_response['model_used']}{personality_note}"
        
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=external_api_chat,
            model_name="external-api-v3",
            provider_name="ExternalAPI"
        )
        
        response = ai.chat("Test external integration", temperature=0.8)
        
        assert "External API response" in response
        assert "external-api-v3" in response
        assert "(with helpful personality)" in response
    
    def test_generic_multi_model_simulation(self):
        """Test generic provider that supports multiple models"""
        class MultiModelAI:
            def __init__(self):
                self.models = {
                    "fast": "Quick response",
                    "smart": "Detailed intelligent response", 
                    "creative": "Creative and imaginative response"
                }
            
            def chat(self, messages, model, **kwargs):
                user_msg = messages[-1]["content"] if messages else "No message"
                
                if model in self.models:
                    return f"{self.models[model]}: {user_msg}"
                else:
                    return f"Unknown model {model}. Using default: {user_msg}"
        
        multi_ai = MultiModelAI()
        
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=multi_ai.chat,
            model_name="smart",  # Default model
            provider_name="MultiModelAI"
        )
        
        # Test different models
        response1 = ai.chat("Hello", model="fast")
        assert "Quick response" in response1
        
        response2 = ai.chat("Hello", model="smart") 
        assert "Detailed intelligent" in response2
        
        response3 = ai.chat("Hello", model="creative")
        assert "Creative and imaginative" in response3
        
        response4 = ai.chat("Hello")  # Should use default
        assert "Detailed intelligent" in response4
    
    def test_generic_conversation_history(self):
        """Test conversation history with generic provider"""
        conversation_history = []
        
        def history_aware_chat(messages, model, **kwargs):
            # Store messages in external history
            conversation_history.extend(messages)
            
            # Count user messages to simulate conversation awareness
            user_messages = [msg for msg in messages if msg["role"] == "user"]
            
            if len(user_messages) == 1:
                return "Nice to meet you!"
            elif len(user_messages) > 1:
                return f"We've been talking for {len(user_messages)} exchanges."
            else:
                return "Hello!"
        
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=history_aware_chat,
            model_name="history-aware",
            provider_name="HistoryAI"
        )
        
        # Test conversation with history
        response1 = ai.chat("Hello", use_history=True)
        assert response1 == "Nice to meet you!"
        
        response2 = ai.chat("How are you?", use_history=True)
        assert "2 exchanges" in response2
        
        response3 = ai.chat("What's the weather?", use_history=True) 
        assert "3 exchanges" in response3
    
    def test_generic_custom_parameters(self):
        """Test passing custom parameters through generic provider"""
        captured_params = {}
        
        def param_aware_chat(messages, model, **kwargs):
            captured_params.clear()
            captured_params.update(kwargs)
            
            user_msg = messages[-1]["content"] if messages else ""
            return f"Response with {len(kwargs)} custom parameters: {user_msg}"
        
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=param_aware_chat,
            model_name="param-test",
            provider_name="ParamAI"
        )
        
        # Test with custom parameters
        ai.chat("Test", temperature=0.9, max_length=100, custom_param="test_value")
        
        assert captured_params["temperature"] == 0.9
        assert captured_params["max_length"] == 100
        assert captured_params["custom_param"] == "test_value"
    
    def test_generic_error_simulation(self):
        """Test error handling with generic provider"""
        def error_prone_chat(messages, model, **kwargs):
            user_msg = messages[-1]["content"] if messages else ""
            
            if "error" in user_msg.lower():
                raise ValueError("Simulated AI error")
            elif "timeout" in user_msg.lower():
                raise TimeoutError("Simulated timeout")
            else:
                return "Normal response"
        
        ai = PersonalityAI(self.test_personality)
        ai.set_provider(
            "generic",
            chat_function=error_prone_chat,
            model_name="error-test",
            provider_name="ErrorAI"
        )
        
        # Test normal operation
        response = ai.chat("Hello")
        assert response == "Normal response"
        
        # Test error conditions
        with pytest.raises(ValueError, match="Simulated AI error"):
            ai.chat("Trigger error")
        
        with pytest.raises(TimeoutError, match="Simulated timeout"):
            ai.chat("Trigger timeout")
    
    def test_generic_multiple_personalities(self):
        """Test generic provider with multiple personalities"""
        def personality_aware_chat(messages, model, **kwargs):
            system_prompt = ""
            user_msg = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"].lower()
                elif msg["role"] == "user":
                    user_msg = msg["content"]
            
            # Respond differently based on personality traits in system prompt
            if "creative" in system_prompt and "creativity" in system_prompt:
                return f"✨ Creative response: {user_msg} sparks my imagination!"
            elif "technical" in system_prompt and "expertise" in system_prompt:
                return f"💻 Technical analysis: {user_msg} requires systematic approach."
            elif "helpful" in system_prompt:
                return f"🤝 I'm here to help with: {user_msg}"
            else:
                return f"Standard response: {user_msg}"
        
        # Test different personalities
        personalities = [
            ("creative_writer", "sparks my imagination"),
            ("technical_mentor", "systematic approach"),
            ("helpful_assistant", "I'm here to help")
        ]
        
        for personality_name, expected_phrase in personalities:
            ai = PersonalityAI(PERSONALITY_TEMPLATES[personality_name])
            ai.set_provider(
                "generic",
                chat_function=personality_aware_chat,
                model_name="personality-aware",
                provider_name="PersonalityAI"
            )
            
            response = ai.chat("Test message")
            assert expected_phrase in response, f"Expected '{expected_phrase}' in response for {personality_name}"
    
    def test_generic_provider_defaults(self):
        """Test generic provider with default values"""
        def simple_chat(messages, model, **kwargs):
            return f"Response from {model}"
        
        # Test with minimal parameters
        provider = create_provider("generic", chat_function=simple_chat)
        
        assert provider.provider_name == "generic"
        assert provider.default_model == "custom"
        
        response = provider.chat([{"role": "user", "content": "test"}])
        assert response == "Response from custom"
        
        # Test with custom defaults
        provider2 = create_provider(
            "generic",
            chat_function=simple_chat,
            model_name="my-model",
            provider_name="my-ai"
        )
        
        assert provider2.provider_name == "my-ai"
        assert provider2.default_model == "my-model"


@pytest.mark.integration 
class TestGenericIntegration:
    """Integration tests for generic provider with real-world scenarios"""
    
    def test_generic_wrapper_for_existing_ai(self):
        """Test wrapping an existing AI system with generic provider"""
        class ExistingAISystem:
            """Simulate an existing AI system with different interface"""
            
            def __init__(self, system_personality="neutral"):
                self.personality = system_personality
                self.conversation_log = []
            
            def generate_response(self, prompt, context=None, settings=None):
                """Existing AI system's method"""
                settings = settings or {}
                
                # Log interaction
                self.conversation_log.append({
                    "prompt": prompt,
                    "context": context,
                    "settings": settings
                })
                
                # Generate response based on personality
                if self.personality == "helpful":
                    return f"I'd be happy to help with: {prompt}"
                elif self.personality == "technical":
                    return f"Technical analysis of: {prompt}"
                else:
                    return f"Response to: {prompt}"
        
        # Create wrapper function for existing AI
        existing_ai = ExistingAISystem(system_personality="helpful")
        
        def wrapper_function(messages, model, **kwargs):
            """Wrapper to adapt Callosum interface to existing AI"""
            
            # Extract messages
            context = []
            current_prompt = ""
            
            for msg in messages:
                if msg["role"] == "system":
                    context.append(f"SYSTEM: {msg['content']}")
                elif msg["role"] == "user":
                    current_prompt = msg["content"]
                elif msg["role"] == "assistant":
                    context.append(f"AI: {msg['content']}")
            
            # Call existing AI system
            return existing_ai.generate_response(
                prompt=current_prompt,
                context="\n".join(context) if context else None,
                settings=kwargs
            )
        
        # Use with PersonalityAI
        ai = PersonalityAI(PERSONALITY_TEMPLATES["helpful_assistant"])
        ai.set_provider(
            "generic",
            chat_function=wrapper_function,
            model_name="existing-ai-v1",
            provider_name="WrappedAI"
        )
        
        # Test the integration
        response = ai.chat("Help me learn Python", temperature=0.7)
        assert "I'd be happy to help" in response
        assert "Help me learn Python" in response
        
        # Check that settings were passed through
        assert len(existing_ai.conversation_log) == 1
        assert existing_ai.conversation_log[0]["settings"]["temperature"] == 0.7
        
        print(f"✅ Successfully wrapped existing AI system: {response}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
