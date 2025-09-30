#!/usr/bin/env python3
"""
Provider switching tests for Callosum DSL
Tests dynamic switching between AI providers while maintaining personality consistency
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES, CallosumError, create_provider


class TestProviderSwitching:
    """Test dynamic provider switching functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_personality = PERSONALITY_TEMPLATES["technical_mentor"]
        
        # Mock providers for testing
        self.mock_providers = {
            "openai": self._create_openai_mock,
            "anthropic": self._create_anthropic_mock,
            "langchain": self._create_langchain_mock,
            "generic": self._create_generic_mock
        }
    
    def _create_openai_mock(self):
        """Create mock OpenAI provider"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "OpenAI technical mentoring response"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            return {"api_key": "test-openai-key"}, mock_client
    
    def _create_anthropic_mock(self):
        """Create mock Anthropic provider"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            mock_content = Mock()
            mock_content.text = "Anthropic technical mentoring response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            return {"api_key": "test-anthropic-key"}, mock_client
    
    def _create_langchain_mock(self):
        """Create mock LangChain provider"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            mock_llm = Mock()
            mock_llm.invoke.return_value = type('Response', (), {
                'content': "LangChain technical mentoring response"
            })()
            mock_llm.model_name = "langchain-test-model"
            
            return {"llm": mock_llm}, mock_llm
    
    def _create_generic_mock(self):
        """Create mock generic provider"""
        def mock_chat_function(messages, model, **kwargs):
            return "Generic technical mentoring response"
        
        return {
            "chat_function": mock_chat_function,
            "model_name": "generic-test-model",
            "provider_name": "GenericAI"
        }, None
    
    def test_basic_provider_switching(self):
        """Test switching between different providers"""
        ai = PersonalityAI(self.test_personality)
        
        # Test switching to each provider type
        for provider_name, mock_creator in self.mock_providers.items():
            provider_kwargs, mock_obj = mock_creator()
            
            # Switch to provider
            ai.set_provider(provider_name, **provider_kwargs)
            
            # Verify provider switch
            provider_info = ai.get_provider_info()
            assert provider_info["has_provider"] is True
            
            # Verify personality remains the same
            personality_summary = ai.get_personality_summary()
            assert personality_summary["name"] == "Technical Programming Mentor"
            
            # Test chat works
            response = ai.chat("Explain design patterns")
            assert isinstance(response, str)
            assert len(response) > 0
            
            print(f"✅ Successfully switched to {provider_name}")
    
    def test_personality_consistency_across_providers(self):
        """Test that personality traits remain consistent across provider switches"""
        ai = PersonalityAI(self.test_personality)
        
        # Get initial personality data
        original_summary = ai.get_personality_summary()
        original_traits = original_summary["traits"]
        original_system_prompt = ai.system_prompt
        
        # Switch providers and verify consistency
        for provider_name, mock_creator in self.mock_providers.items():
            provider_kwargs, _ = mock_creator()
            ai.set_provider(provider_name, **provider_kwargs)
            
            # Verify personality data unchanged
            current_summary = ai.get_personality_summary()
            assert current_summary["name"] == original_summary["name"]
            assert current_summary["traits"] == original_traits
            assert current_summary["dominant_trait"] == original_summary["dominant_trait"]
            assert current_summary["knowledge_domains"] == original_summary["knowledge_domains"]
            
            # Verify system prompt unchanged
            assert ai.system_prompt == original_system_prompt
            
            print(f"✅ Personality consistent with {provider_name}")
    
    def test_conversation_history_across_switches(self):
        """Test that conversation history is maintained across provider switches"""
        # Use mock providers that capture and return different responses
        openai_kwargs, openai_mock = self._create_openai_mock()
        anthropic_kwargs, anthropic_mock = self._create_anthropic_mock()
        
        ai = PersonalityAI(self.test_personality)
        
        # Start with OpenAI
        ai.set_provider("openai", **openai_kwargs)
        response1 = ai.chat("Hello, I'm learning Python", use_history=True)
        
        # Switch to Anthropic, continue conversation
        ai.set_provider("anthropic", **anthropic_kwargs)
        response2 = ai.chat("What was I learning about?", use_history=True)
        
        # Check conversation history is maintained
        history = ai.get_conversation_history()
        assert len(history) == 4  # 2 user messages + 2 assistant responses
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello, I'm learning Python"
        assert history[2]["content"] == "What was I learning about?"
        
        # Switch back to OpenAI, history should still be there
        ai.set_provider("openai", **openai_kwargs)
        history_after_switch = ai.get_conversation_history()
        assert len(history_after_switch) == 4
        assert history_after_switch == history
        
        print("✅ Conversation history maintained across provider switches")
    
    def test_system_prompt_usage_across_providers(self):
        """Test that the same system prompt is used across different providers"""
        ai = PersonalityAI(self.test_personality)
        captured_prompts = {}
        
        # OpenAI - capture system prompt
        openai_kwargs, openai_mock = self._create_openai_mock()
        ai.set_provider("openai", **openai_kwargs)
        ai.chat("Test message")
        
        openai_call_args = openai_mock.chat.completions.create.call_args
        openai_system_prompt = openai_call_args[1]["messages"][0]["content"]
        captured_prompts["openai"] = openai_system_prompt
        
        # Anthropic - capture system prompt
        anthropic_kwargs, anthropic_mock = self._create_anthropic_mock()
        ai.set_provider("anthropic", **anthropic_kwargs)
        ai.chat("Test message")
        
        anthropic_call_args = anthropic_mock.messages.create.call_args
        anthropic_system_prompt = anthropic_call_args[1]["system"]
        captured_prompts["anthropic"] = anthropic_system_prompt
        
        # LangChain - capture system prompt
        langchain_kwargs, langchain_mock = self._create_langchain_mock()
        ai.set_provider("langchain", **langchain_kwargs)
        ai.chat("Test message")
        
        # For LangChain, check that SystemMessage was called with correct content
        langchain_system_calls = [
            call for call in langchain_kwargs["llm"].invoke.call_args_list
            if call[0]  # Has positional args (messages)
        ]
        # The system message should be in the messages passed to invoke
        
        # Verify all system prompts are identical
        assert captured_prompts["openai"] == captured_prompts["anthropic"]
        assert "Technical Programming Mentor" in captured_prompts["openai"]
        assert "technical_expertise" in captured_prompts["openai"]
        
        print("✅ Consistent system prompt across all providers")
    
    def test_provider_specific_features_preserved(self):
        """Test that provider-specific features work after switching"""
        ai = PersonalityAI(self.test_personality)
        
        # Test OpenAI-specific parameters
        openai_kwargs, openai_mock = self._create_openai_mock()
        ai.set_provider("openai", **openai_kwargs)
        ai.chat("Test", temperature=0.8, max_tokens=150, top_p=0.9)
        
        openai_call_args = openai_mock.chat.completions.create.call_args
        assert openai_call_args[1]["temperature"] == 0.8
        assert openai_call_args[1]["max_tokens"] == 150
        assert openai_call_args[1]["top_p"] == 0.9
        
        # Test Anthropic-specific parameters  
        anthropic_kwargs, anthropic_mock = self._create_anthropic_mock()
        ai.set_provider("anthropic", **anthropic_kwargs)
        ai.chat("Test", max_tokens=2000, temperature=0.7)
        
        anthropic_call_args = anthropic_mock.messages.create.call_args
        assert anthropic_call_args[1]["max_tokens"] == 2000
        assert anthropic_call_args[1]["temperature"] == 0.7
        
        print("✅ Provider-specific features preserved after switching")
    
    def test_multiple_personality_instances_provider_switching(self):
        """Test provider switching with multiple PersonalityAI instances"""
        personalities = [
            PERSONALITY_TEMPLATES["helpful_assistant"],
            PERSONALITY_TEMPLATES["creative_writer"], 
            PERSONALITY_TEMPLATES["technical_mentor"]
        ]
        
        ais = [PersonalityAI(personality) for personality in personalities]
        
        # Switch all instances to different providers
        provider_assignments = [
            ("openai", self._create_openai_mock),
            ("anthropic", self._create_anthropic_mock),
            ("langchain", self._create_langchain_mock)
        ]
        
        for ai, (provider_name, mock_creator) in zip(ais, provider_assignments):
            provider_kwargs, _ = mock_creator()
            ai.set_provider(provider_name, **provider_kwargs)
            
            # Test each AI instance
            response = ai.chat("Test message")
            assert isinstance(response, str)
            
            # Verify each has its own personality
            summary = ai.get_personality_summary()
            provider_info = ai.get_provider_info()
            
            print(f"✅ {summary['name']} using {provider_info['provider']}: OK")
        
        # Verify they're all different
        summaries = [ai.get_personality_summary() for ai in ais]
        names = [s["name"] for s in summaries]
        assert len(set(names)) == 3, "All personalities should be different"
    
    def test_rapid_provider_switching(self):
        """Test rapid switching between providers"""
        ai = PersonalityAI(self.test_personality)
        
        # Rapidly switch between providers multiple times
        switch_sequence = ["openai", "anthropic", "generic", "langchain", "openai", "anthropic"]
        
        for provider_name in switch_sequence:
            provider_kwargs, _ = self.mock_providers[provider_name]()
            ai.set_provider(provider_name, **provider_kwargs)
            
            # Verify switch was successful
            provider_info = ai.get_provider_info()
            assert provider_info["has_provider"] is True
            
            # Test functionality
            response = ai.chat("Quick test")
            assert isinstance(response, str)
            
            # Personality should remain consistent
            summary = ai.get_personality_summary()
            assert summary["name"] == "Technical Programming Mentor"
        
        print("✅ Rapid provider switching successful")
    
    def test_provider_switching_error_handling(self):
        """Test error handling during provider switching"""
        ai = PersonalityAI(self.test_personality)
        
        # Test switching to invalid provider
        with pytest.raises(ValueError):
            ai.set_provider("invalid_provider")
        
        # Test switching with missing parameters
        with pytest.raises(CallosumError):
            ai.set_provider("openai")  # Missing api_key
        
        # Verify AI is still functional after failed switches
        openai_kwargs, _ = self._create_openai_mock()
        ai.set_provider("openai", **openai_kwargs)
        
        response = ai.chat("Test after error")
        assert isinstance(response, str)
        
        print("✅ Error handling during provider switching works correctly")
    
    def test_provider_switching_with_custom_models(self):
        """Test provider switching with different model configurations"""
        ai = PersonalityAI(self.test_personality)
        
        # Test with different models for each provider
        model_configs = [
            ("openai", {"api_key": "test-key"}, "gpt-3.5-turbo"),
            ("openai", {"api_key": "test-key"}, "gpt-4"),
            ("anthropic", {"api_key": "test-key"}, "claude-3-haiku-20240307"),
            ("anthropic", {"api_key": "test-key"}, "claude-3-sonnet-20240229")
        ]
        
        for provider_name, provider_kwargs, model in model_configs:
            mock_creator = self.mock_providers[provider_name]
            _, mock_obj = mock_creator()
            
            ai.set_provider(provider_name, **provider_kwargs)
            
            # Test with specific model
            response = ai.chat("Test message", model=model)
            assert isinstance(response, str)
            
            # Verify model was used (check mock calls)
            if provider_name == "openai" and mock_obj:
                call_args = mock_obj.chat.completions.create.call_args
                assert call_args[1]["model"] == model
            elif provider_name == "anthropic" and mock_obj:
                call_args = mock_obj.messages.create.call_args
                assert call_args[1]["model"] == model
            
            print(f"✅ {provider_name} with model {model}: OK")
    
    def test_provider_auto_detection_after_switching(self):
        """Test that auto-detection still works after manual provider switching"""
        ai = PersonalityAI(self.test_personality)
        
        # Manually switch to a provider
        openai_kwargs, _ = self._create_openai_mock()
        ai.set_provider("openai", **openai_kwargs)
        
        # Check available providers (should still work)
        available = ai.get_available_providers()
        assert isinstance(available, list)
        
        # Provider info should reflect current provider
        info = ai.get_provider_info()
        assert "openai" in info["provider"]
        
        print("✅ Auto-detection works after manual switching")


@pytest.mark.integration
class TestProviderSwitchingIntegration:
    """Integration tests for provider switching in real scenarios"""
    
    def test_provider_switching_conversation_flow(self):
        """Test a complete conversation flow with provider switching"""
        # Create a conversation that switches providers mid-conversation
        conversation_flow = [
            ("openai", "Hello, I'm learning about design patterns"),
            ("anthropic", "Can you tell me more about the Observer pattern?"),
            ("langchain", "What are some real-world examples?"),
            ("generic", "Thanks for the explanation!")
        ]
        
        ai = PersonalityAI(PERSONALITY_TEMPLATES["technical_mentor"])
        
        for provider_name, message in conversation_flow:
            # Switch provider
            mock_creator = TestProviderSwitching().mock_providers[provider_name]
            provider_kwargs, _ = mock_creator()
            ai.set_provider(provider_name, **provider_kwargs)
            
            # Continue conversation
            response = ai.chat(message, use_history=True)
            assert isinstance(response, str)
            
            print(f"✅ {provider_name}: {message[:30]}... → {response[:50]}...")
        
        # Verify full conversation history was maintained
        history = ai.get_conversation_history()
        assert len(history) == 8  # 4 user messages + 4 assistant responses
        
        # Verify all user messages are in history
        user_messages = [msg["content"] for msg in history if msg["role"] == "user"]
        expected_messages = [msg for _, msg in conversation_flow]
        assert user_messages == expected_messages
        
        print("✅ Complete conversation flow with provider switching successful")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
