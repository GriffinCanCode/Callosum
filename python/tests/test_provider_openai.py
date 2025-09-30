#!/usr/bin/env python3
"""
OpenAI provider tests for Callosum DSL
Tests OpenAI integration with various personalities and scenarios
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES, CallosumError, create_provider


class TestOpenAIProvider:
    """Test OpenAI provider functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_personality = PERSONALITY_TEMPLATES["helpful_assistant"]
        self.mock_api_key = "test-openai-key-12345"
        
    def test_openai_provider_creation(self):
        """Test OpenAI provider creation"""
        with patch('openai.OpenAI') as mock_openai:
            provider = create_provider("openai", api_key=self.mock_api_key)
            
            assert provider.provider_name == "openai"
            assert provider.default_model == "gpt-4"
            mock_openai.assert_called_once_with(api_key=self.mock_api_key)
    
    def test_openai_provider_missing_package(self):
        """Test error when OpenAI package is missing"""
        with patch.dict('sys.modules', {'openai': None}):
            with pytest.raises(CallosumError, match="OpenAI package not installed"):
                create_provider("openai", api_key=self.mock_api_key)
    
    def test_openai_provider_chat(self):
        """Test OpenAI provider chat functionality"""
        with patch('openai.OpenAI') as mock_openai_class:
            # Setup mock
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Test response from OpenAI"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test
            provider = create_provider("openai", api_key=self.mock_api_key)
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ]
            
            response = provider.chat(messages, model="gpt-4")
            
            assert response == "Test response from OpenAI"
            mock_client.chat.completions.create.assert_called_once_with(
                model="gpt-4",
                messages=messages
            )
    
    def test_personality_ai_with_openai(self):
        """Test PersonalityAI with OpenAI provider"""
        with patch('openai.OpenAI') as mock_openai_class:
            # Setup mock
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Hello! I'm a helpful AI assistant with empathy."
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            # Create PersonalityAI with OpenAI
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("openai", api_key=self.mock_api_key)
            
            # Test provider info
            provider_info = ai.get_provider_info()
            assert provider_info["provider"] == "openai"
            assert provider_info["default_model"] == "gpt-4"
            assert provider_info["has_provider"] is True
            
            # Test chat
            response = ai.chat("Hello!")
            assert response == "Hello! I'm a helpful AI assistant with empathy."
            
            # Verify system prompt was included
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert "Helpful AI Assistant" in messages[0]["content"]
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Hello!"
    
    def test_openai_conversation_history(self):
        """Test conversation history with OpenAI"""
        with patch('openai.OpenAI') as mock_openai_class:
            # Setup mock
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock responses
            responses = [
                "Hello! How can I help you?",
                "You asked me about Python. It's a great language!"
            ]
            
            def mock_create(*args, **kwargs):
                mock_response = Mock()
                mock_choice = Mock()
                mock_message = Mock()
                mock_message.content = responses[mock_create.call_count - 1]
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                return mock_response
            
            mock_create.call_count = 0
            def side_effect(*args, **kwargs):
                mock_create.call_count += 1
                return mock_create(*args, **kwargs)
            
            mock_client.chat.completions.create.side_effect = side_effect
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("openai", api_key=self.mock_api_key)
            
            # First message
            response1 = ai.chat("Hello", use_history=True)
            assert response1 == "Hello! How can I help you?"
            
            # Second message with history
            response2 = ai.chat("Tell me about Python", use_history=True)
            assert response2 == "You asked me about Python. It's a great language!"
            
            # Check history was maintained
            history = ai.get_conversation_history()
            assert len(history) == 4  # 2 user messages + 2 assistant responses
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "Hello"
            assert history[1]["role"] == "assistant"
            assert history[2]["content"] == "Tell me about Python"
    
    def test_openai_model_switching(self):
        """Test switching between OpenAI models"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Response"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("openai", api_key=self.mock_api_key)
            
            # Test with different models
            ai.chat("Hello", model="gpt-3.5-turbo")
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            
            ai.chat("Hello", model="gpt-4")
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4"
            
            # Test default model
            ai.chat("Hello")
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-4"  # Default model
    
    def test_openai_custom_parameters(self):
        """Test passing custom parameters to OpenAI"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Response"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("openai", api_key=self.mock_api_key)
            
            # Test with custom parameters
            ai.chat("Hello", temperature=0.8, max_tokens=150, top_p=0.9)
            
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["temperature"] == 0.8
            assert call_args[1]["max_tokens"] == 150
            assert call_args[1]["top_p"] == 0.9
    
    def test_multiple_personalities_openai(self):
        """Test multiple personalities with OpenAI"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Mock response
            mock_response = Mock()
            mock_choice = Mock()
            mock_message = Mock()
            mock_message.content = "Response"
            mock_choice.message = mock_message
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test different personalities
            personalities = [
                PERSONALITY_TEMPLATES["helpful_assistant"],
                PERSONALITY_TEMPLATES["creative_writer"],
                PERSONALITY_TEMPLATES["technical_mentor"]
            ]
            
            ais = []
            for personality in personalities:
                ai = PersonalityAI(personality)
                ai.set_provider("openai", api_key=self.mock_api_key)
                ais.append(ai)
            
            # Test each personality generates different system prompts
            prompts = []
            for ai in ais:
                ai.chat("Test")
                call_args = mock_client.chat.completions.create.call_args
                messages = call_args[1]["messages"]
                system_prompt = messages[0]["content"]
                prompts.append(system_prompt)
            
            # All prompts should be different
            assert len(set(prompts)) == 3, "Each personality should generate unique system prompts"
    
    def test_openai_error_handling(self):
        """Test OpenAI error handling"""
        with patch('openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Test API error
            from openai import OpenAIError
            mock_client.chat.completions.create.side_effect = OpenAIError("API Error")
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("openai", api_key=self.mock_api_key)
            
            with pytest.raises(OpenAIError):
                ai.chat("Hello")


@pytest.mark.integration
class TestOpenAIIntegration:
    """Integration tests for OpenAI provider (requires actual API key)"""
    
    def setup_method(self):
        """Setup for integration tests"""
        # Load environment variables from .env file in tests directory
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")
    
    def test_real_openai_integration(self):
        """Test with real OpenAI API (requires OPENAI_API_KEY)"""
        ai = PersonalityAI(PERSONALITY_TEMPLATES["helpful_assistant"])
        ai.set_provider("openai", api_key=self.api_key)
        
        response = ai.chat("Say hello in exactly 5 words", max_tokens=20)
        
        # Basic checks
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        print(f"OpenAI Response: {response}")
    
    def test_real_openai_conversation(self):
        """Test conversation with real OpenAI API"""
        ai = PersonalityAI(PERSONALITY_TEMPLATES["technical_mentor"])
        ai.set_provider("openai", api_key=self.api_key)
        
        # Start conversation
        response1 = ai.chat("Hello, I'm learning Python", use_history=True, max_tokens=50)
        response2 = ai.chat("What was I learning?", use_history=True, max_tokens=30)
        
        # Check responses
        assert isinstance(response1, str)
        assert isinstance(response2, str)
        assert "python" in response2.lower(), "Should remember Python from conversation"
        
        print(f"Response 1: {response1}")
        print(f"Response 2: {response2}")


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
