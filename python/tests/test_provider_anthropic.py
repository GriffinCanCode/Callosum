#!/usr/bin/env python3
"""
Anthropic provider tests for Callosum DSL
Tests Anthropic Claude integration with various personalities and scenarios
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES, CallosumError, create_provider


class TestAnthropicProvider:
    """Test Anthropic provider functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_personality = PERSONALITY_TEMPLATES["creative_writer"]
        self.mock_api_key = "test-anthropic-key-12345"
        
    def test_anthropic_provider_creation(self):
        """Test Anthropic provider creation"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            provider = create_provider("anthropic", api_key=self.mock_api_key)
            
            assert provider.provider_name == "anthropic"
            assert provider.default_model == "claude-3-sonnet-20240229"
            mock_anthropic.assert_called_once_with(api_key=self.mock_api_key)
    
    def test_anthropic_provider_missing_package(self):
        """Test error when Anthropic package is missing"""
        with patch.dict('sys.modules', {'anthropic': None}):
            with pytest.raises(CallosumError, match="Anthropic package not installed"):
                create_provider("anthropic", api_key=self.mock_api_key)
    
    def test_anthropic_provider_chat(self):
        """Test Anthropic provider chat functionality"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            # Setup mock
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            # Mock response for Anthropic (different structure than OpenAI)
            mock_content = Mock()
            mock_content.text = "Test response from Claude"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            # Test
            provider = create_provider("anthropic", api_key=self.mock_api_key)
            messages = [
                {"role": "system", "content": "You are a creative writer"},
                {"role": "user", "content": "Write a poem"}
            ]
            
            response = provider.chat(messages, model="claude-3-haiku-20240307")
            
            assert response == "Test response from Claude"
            
            # Check that system message was separated from other messages
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["model"] == "claude-3-haiku-20240307"
            assert call_args[1]["max_tokens"] == 1000  # Default
            assert call_args[1]["system"] == "You are a creative writer"
            assert len(call_args[1]["messages"]) == 1
            assert call_args[1]["messages"][0]["role"] == "user"
    
    def test_anthropic_system_message_handling(self):
        """Test proper system message handling for Anthropic"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            mock_content = Mock()
            mock_content.text = "Response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            provider = create_provider("anthropic", api_key=self.mock_api_key)
            
            # Test with system message in middle of conversation
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "system", "content": "Be helpful"},
                {"role": "user", "content": "Help me"}
            ]
            
            provider.chat(messages)
            
            call_args = mock_client.messages.create.call_args
            # System message should be extracted
            assert call_args[1]["system"] == "Be helpful"
            # Only user/assistant messages should remain
            assert len(call_args[1]["messages"]) == 3
            assert all(msg["role"] in ["user", "assistant"] for msg in call_args[1]["messages"])
    
    def test_personality_ai_with_anthropic(self):
        """Test PersonalityAI with Anthropic provider"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            # Setup mock
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            # Mock response
            mock_content = Mock()
            mock_content.text = "I am Claude, a creative writing companion. I love crafting stories!"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            # Create PersonalityAI with Anthropic
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("anthropic", api_key=self.mock_api_key)
            
            # Test provider info
            provider_info = ai.get_provider_info()
            assert provider_info["provider"] == "anthropic"
            assert provider_info["default_model"] == "claude-3-sonnet-20240229"
            assert provider_info["has_provider"] is True
            
            # Test chat
            response = ai.chat("Write me a story!")
            assert response == "I am Claude, a creative writing companion. I love crafting stories!"
            
            # Verify system prompt was used correctly
            call_args = mock_client.messages.create.call_args
            assert "Creative Writing Companion" in call_args[1]["system"]
            assert len(call_args[1]["messages"]) == 1
            assert call_args[1]["messages"][0]["role"] == "user"
            assert call_args[1]["messages"][0]["content"] == "Write me a story!"
    
    def test_anthropic_conversation_history(self):
        """Test conversation history with Anthropic"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            # Setup mock
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            # Mock responses
            responses = [
                "Hello! I'm excited to help with creative writing!",
                "You mentioned poetry earlier. Let me write a haiku for you."
            ]
            
            def mock_create(*args, **kwargs):
                mock_content = Mock()
                mock_content.text = responses[mock_create.call_count - 1]
                mock_response = Mock()
                mock_response.content = [mock_content]
                return mock_response
            
            mock_create.call_count = 0
            def side_effect(*args, **kwargs):
                mock_create.call_count += 1
                return mock_create(*args, **kwargs)
            
            mock_client.messages.create.side_effect = side_effect
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("anthropic", api_key=self.mock_api_key)
            
            # First message
            response1 = ai.chat("Hello, I love poetry", use_history=True)
            assert response1 == "Hello! I'm excited to help with creative writing!"
            
            # Second message with history
            response2 = ai.chat("Write something short", use_history=True)
            assert response2 == "You mentioned poetry earlier. Let me write a haiku for you."
            
            # Check that conversation history was passed to Anthropic
            call_args = mock_client.messages.create.call_args
            messages = call_args[1]["messages"]
            
            # Should have: user1, assistant1, user2
            assert len(messages) == 3
            assert messages[0]["content"] == "Hello, I love poetry"
            assert messages[1]["content"] == "Hello! I'm excited to help with creative writing!"
            assert messages[2]["content"] == "Write something short"
    
    def test_anthropic_custom_parameters(self):
        """Test passing custom parameters to Anthropic"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            mock_content = Mock()
            mock_content.text = "Response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("anthropic", api_key=self.mock_api_key)
            
            # Test with custom parameters
            ai.chat("Hello", max_tokens=2000, temperature=0.7)
            
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["max_tokens"] == 2000
            assert call_args[1]["temperature"] == 0.7
    
    def test_anthropic_model_switching(self):
        """Test switching between Anthropic models"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            mock_content = Mock()
            mock_content.text = "Response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("anthropic", api_key=self.mock_api_key)
            
            # Test with different models
            ai.chat("Hello", model="claude-3-haiku-20240307")
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["model"] == "claude-3-haiku-20240307"
            
            ai.chat("Hello", model="claude-3-opus-20240229")
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["model"] == "claude-3-opus-20240229"
            
            # Test default model
            ai.chat("Hello")
            call_args = mock_client.messages.create.call_args
            assert call_args[1]["model"] == "claude-3-sonnet-20240229"
    
    def test_multiple_personalities_anthropic(self):
        """Test multiple personalities with Anthropic"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            mock_content = Mock()
            mock_content.text = "Response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            # Test different personalities
            personalities = [
                PERSONALITY_TEMPLATES["helpful_assistant"],
                PERSONALITY_TEMPLATES["creative_writer"],
                PERSONALITY_TEMPLATES["technical_mentor"]
            ]
            
            ais = []
            for personality in personalities:
                ai = PersonalityAI(personality)
                ai.set_provider("anthropic", api_key=self.mock_api_key)
                ais.append(ai)
            
            # Test each personality generates different system prompts
            system_prompts = []
            for ai in ais:
                ai.chat("Test")
                call_args = mock_client.messages.create.call_args
                system_prompt = call_args[1]["system"]
                system_prompts.append(system_prompt)
            
            # All prompts should be different
            assert len(set(system_prompts)) == 3, "Each personality should generate unique system prompts"
            
            # Check specific personality elements
            assert "Helpful AI Assistant" in system_prompts[0]
            assert "Creative Writing Companion" in system_prompts[1]
            assert "Technical Programming Mentor" in system_prompts[2]
    
    def test_anthropic_no_system_message(self):
        """Test Anthropic with messages that have no system message"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            mock_content = Mock()
            mock_content.text = "Response"
            mock_response = Mock()
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            
            provider = create_provider("anthropic", api_key=self.mock_api_key)
            
            # Test with no system message
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
                {"role": "user", "content": "How are you?"}
            ]
            
            provider.chat(messages)
            
            call_args = mock_client.messages.create.call_args
            # System should be None
            assert call_args[1]["system"] is None
            # All messages should be preserved
            assert len(call_args[1]["messages"]) == 3
    
    def test_anthropic_error_handling(self):
        """Test Anthropic error handling"""
        with patch('anthropic.Anthropic') as mock_anthropic_class:
            mock_client = Mock()
            mock_anthropic_class.return_value = mock_client
            
            # Test API error
            from anthropic import AnthropicError
            mock_client.messages.create.side_effect = AnthropicError("API Error")
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("anthropic", api_key=self.mock_api_key)
            
            with pytest.raises(AnthropicError):
                ai.chat("Hello")


@pytest.mark.integration
class TestAnthropicIntegration:
    """Integration tests for Anthropic provider (requires actual API key)"""
    
    def setup_method(self):
        """Setup for integration tests"""
        # Load environment variables from .env file in tests directory
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            pytest.skip("ANTHROPIC_API_KEY environment variable not set")
    
    def test_real_anthropic_integration(self):
        """Test with real Anthropic API (requires ANTHROPIC_API_KEY)"""
        ai = PersonalityAI(PERSONALITY_TEMPLATES["creative_writer"])
        ai.set_provider("anthropic", api_key=self.api_key)
        
        response = ai.chat("Write exactly 3 words about creativity", max_tokens=20)
        
        # Basic checks
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        print(f"Anthropic Response: {response}")
    
    def test_real_anthropic_conversation(self):
        """Test conversation with real Anthropic API"""
        ai = PersonalityAI(PERSONALITY_TEMPLATES["helpful_assistant"])
        ai.set_provider("anthropic", api_key=self.api_key)
        
        # Start conversation
        response1 = ai.chat("I'm working on a story", use_history=True, max_tokens=50)
        response2 = ai.chat("What was I working on?", use_history=True, max_tokens=30)
        
        # Check responses
        assert isinstance(response1, str)
        assert isinstance(response2, str)
        assert "story" in response2.lower(), "Should remember story from conversation"
        
        print(f"Response 1: {response1}")
        print(f"Response 2: {response2}")
    
    def test_anthropic_model_comparison(self):
        """Test different Anthropic models with same personality"""
        ai = PersonalityAI(PERSONALITY_TEMPLATES["technical_mentor"])
        ai.set_provider("anthropic", api_key=self.api_key)
        
        models = ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"]
        responses = {}
        
        for model in models:
            response = ai.chat("Explain Python in 10 words", model=model, max_tokens=30)
            responses[model] = response
            print(f"{model}: {response}")
        
        # Both should respond, but may be different
        for model, response in responses.items():
            assert isinstance(response, str)
            assert len(response.strip()) > 0


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
