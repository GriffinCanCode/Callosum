#!/usr/bin/env python3
"""
LangChain provider tests for Callosum DSL
Tests LangChain integration with various models and scenarios
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from callosum_dsl import PersonalityAI, PERSONALITY_TEMPLATES, CallosumError, create_provider


class MockLangChainLLM:
    """Mock LangChain LLM for testing"""
    
    def __init__(self, model_name="mock-model", response="Mock response"):
        self.model_name = model_name
        self.model = model_name  # Some LLMs use .model instead of .model_name
        self._response = response
    
    def invoke(self, messages, **kwargs):
        """Mock invoke method"""
        # Return a mock response object with content
        return type('Response', (), {'content': self._response})()


class MockStreamingLLM:
    """Mock streaming LangChain LLM for testing"""
    
    def __init__(self, model_name="mock-streaming"):
        self.model_name = model_name
    
    def invoke(self, messages, **kwargs):
        return type('Response', (), {'content': "Streaming response"})()
    
    def stream(self, messages, **kwargs):
        # Mock streaming response
        chunks = ["Hello", " from", " streaming", " model"]
        for chunk in chunks:
            yield type('Chunk', (), {'content': chunk})()


class TestLangChainProvider:
    """Test LangChain provider functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.test_personality = PERSONALITY_TEMPLATES["technical_mentor"]
        
    def test_langchain_provider_creation(self):
        """Test LangChain provider creation"""
        with patch('langchain_core.messages.SystemMessage'):
            with patch('langchain_core.messages.HumanMessage'):
                with patch('langchain_core.messages.AIMessage'):
                    mock_llm = MockLangChainLLM("test-model")
                    provider = create_provider("langchain", llm=mock_llm)
                    
                    assert provider.provider_name == "langchain-mocklangchainllm"
                    assert provider.default_model == "test-model"
    
    def test_langchain_provider_missing_llm(self):
        """Test error when LLM is not provided"""
        with patch('langchain_core.messages.SystemMessage'):
            with patch('langchain_core.messages.HumanMessage'):
                with patch('langchain_core.messages.AIMessage'):
                    with pytest.raises(ValueError, match="LangChain LLM instance is required"):
                        create_provider("langchain", llm=None)
    
    def test_langchain_provider_invalid_llm(self):
        """Test error when invalid LLM is provided"""
        with patch('langchain_core.messages.SystemMessage'):
            with patch('langchain_core.messages.HumanMessage'):
                with patch('langchain_core.messages.AIMessage'):
                    invalid_llm = object()  # Object without invoke method
                    with pytest.raises(ValueError, match="must have an 'invoke' method"):
                        create_provider("langchain", llm=invalid_llm)
    
    def test_langchain_provider_missing_package(self):
        """Test error when LangChain package is missing"""
        with patch.dict('sys.modules', {'langchain_core': None}):
            with pytest.raises(CallosumError, match="LangChain not installed"):
                create_provider("langchain", llm=MockLangChainLLM())
    
    def test_langchain_provider_chat(self):
        """Test LangChain provider chat functionality"""
        with patch('langchain_core.messages') as mock_messages:
            # Setup message class mocks
            mock_system = Mock()
            mock_human = Mock()
            mock_ai = Mock()
            mock_messages.SystemMessage = mock_system
            mock_messages.HumanMessage = mock_human
            mock_messages.AIMessage = mock_ai
            
            # Create provider
            mock_llm = MockLangChainLLM("gpt-4", "LangChain response")
            provider = create_provider("langchain", llm=mock_llm)
            
            # Test chat
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
            
            response = provider.chat(messages)
            assert response == "LangChain response"
            
            # Verify message conversion
            assert mock_system.called
            assert mock_human.called
            assert mock_ai.called
    
    def test_personality_ai_with_langchain(self):
        """Test PersonalityAI with LangChain provider"""
        with patch('langchain_core.messages') as mock_messages:
            # Setup message class mocks
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Create LLM mock
            mock_llm = MockLangChainLLM("technical-model", "I'm here to help with technical questions!")
            
            # Create PersonalityAI with LangChain
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            # Test provider info
            provider_info = ai.get_provider_info()
            assert "langchain" in provider_info["provider"].lower()
            assert provider_info["default_model"] == "technical-model"
            assert provider_info["has_provider"] is True
            
            # Test chat
            response = ai.chat("Explain design patterns")
            assert response == "I'm here to help with technical questions!"
    
    def test_langchain_openai_integration(self):
        """Test LangChain with OpenAI models (mocked)"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Mock LangChain OpenAI
            mock_llm = MockLangChainLLM("gpt-4", "OpenAI via LangChain response")
            mock_llm.__class__.__name__ = "ChatOpenAI"
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            provider_info = ai.get_provider_info()
            assert "chatopenai" in provider_info["provider"]
            
            response = ai.chat("Test OpenAI via LangChain")
            assert response == "OpenAI via LangChain response"
    
    def test_langchain_anthropic_integration(self):
        """Test LangChain with Anthropic models (mocked)"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Mock LangChain Anthropic
            mock_llm = MockLangChainLLM("claude-3-sonnet-20240229", "Anthropic via LangChain response")
            mock_llm.__class__.__name__ = "ChatAnthropic"
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            provider_info = ai.get_provider_info()
            assert "chatanthropic" in provider_info["provider"]
            
            response = ai.chat("Test Anthropic via LangChain")
            assert response == "Anthropic via LangChain response"
    
    def test_langchain_local_model_integration(self):
        """Test LangChain with local models (Ollama, etc.)"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Mock local model via LangChain
            mock_llm = MockLangChainLLM("llama2", "Local model via LangChain response")
            mock_llm.__class__.__name__ = "Ollama"
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            provider_info = ai.get_provider_info()
            assert "ollama" in provider_info["provider"]
            
            response = ai.chat("Test local model via LangChain")
            assert response == "Local model via LangChain response"
    
    def test_langchain_conversation_history(self):
        """Test conversation history with LangChain"""
        with patch('langchain_core.messages') as mock_messages:
            # Setup message class mocks that track calls
            system_messages = []
            human_messages = []
            ai_messages = []
            
            def mock_system_init(content):
                system_messages.append(content)
                return Mock(content=content)
            
            def mock_human_init(content):
                human_messages.append(content)
                return Mock(content=content)
            
            def mock_ai_init(content):
                ai_messages.append(content)
                return Mock(content=content)
            
            mock_messages.SystemMessage = mock_system_init
            mock_messages.HumanMessage = mock_human_init
            mock_messages.AIMessage = mock_ai_init
            
            # Mock LLM with different responses
            responses = ["Hello! I'm a technical mentor.", "You asked about Python programming."]
            response_index = [0]
            
            def mock_invoke(messages, **kwargs):
                resp = responses[response_index[0]]
                response_index[0] = (response_index[0] + 1) % len(responses)
                return type('Response', (), {'content': resp})()
            
            mock_llm = Mock()
            mock_llm.invoke = mock_invoke
            mock_llm.model_name = "test-model"
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            # First message
            response1 = ai.chat("Hello", use_history=True)
            assert response1 == "Hello! I'm a technical mentor."
            
            # Second message with history
            response2 = ai.chat("Tell me about Python", use_history=True)
            assert response2 == "You asked about Python programming."
            
            # Check that proper messages were created
            assert len(human_messages) >= 2
            assert "Hello" in human_messages
            assert "Tell me about Python" in human_messages
            assert len(ai_messages) >= 1  # Assistant response should be in history
    
    def test_langchain_multiple_models_same_personality(self):
        """Test same personality across different LangChain models"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Different mock models
            models = [
                MockLangChainLLM("gpt-4", "GPT-4 response"),
                MockLangChainLLM("claude-3", "Claude response"),
                MockLangChainLLM("llama2", "Llama response")
            ]
            
            personality = PERSONALITY_TEMPLATES["creative_writer"]
            responses = []
            
            for model in models:
                ai = PersonalityAI(personality)
                ai.set_provider("langchain", llm=model)
                response = ai.chat("Write a haiku")
                responses.append(response)
            
            # All should respond
            assert len(responses) == 3
            assert all(isinstance(r, str) for r in responses)
            
            # Responses should be different (from different models)
            expected = ["GPT-4 response", "Claude response", "Llama response"]
            assert responses == expected
    
    def test_langchain_custom_parameters(self):
        """Test passing custom parameters through LangChain"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Mock LLM that captures kwargs
            captured_kwargs = {}
            
            def mock_invoke(messages, **kwargs):
                captured_kwargs.update(kwargs)
                return type('Response', (), {'content': "Response with params"})()
            
            mock_llm = Mock()
            mock_llm.invoke = mock_invoke
            mock_llm.model_name = "test-model"
            
            # Test
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            # Chat with custom parameters
            ai.chat("Hello", temperature=0.7, max_tokens=150, top_p=0.9)
            
            # Check parameters were passed through
            assert captured_kwargs["temperature"] == 0.7
            assert captured_kwargs["max_tokens"] == 150
            assert captured_kwargs["top_p"] == 0.9
    
    def test_langchain_response_types(self):
        """Test different LangChain response types"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            test_cases = [
                # Response with .content attribute
                type('Response', (), {'content': "Content response"})(),
                # Direct string response
                "Direct string response",
                # Other response type (converted to string)
                {"message": "Dict response"}
            ]
            
            for i, response_obj in enumerate(test_cases):
                mock_llm = Mock()
                mock_llm.invoke = Mock(return_value=response_obj)
                mock_llm.model_name = f"test-model-{i}"
                
                ai = PersonalityAI(self.test_personality)
                ai.set_provider("langchain", llm=mock_llm)
                
                response = ai.chat("Test")
                
                if hasattr(response_obj, 'content'):
                    assert response == response_obj.content
                elif isinstance(response_obj, str):
                    assert response == response_obj
                else:
                    assert response == str(response_obj)
    
    def test_langchain_streaming_model(self):
        """Test LangChain with streaming model"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Mock streaming LLM
            mock_llm = MockStreamingLLM("streaming-model")
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            # Regular chat should work even with streaming models
            response = ai.chat("Test streaming")
            assert response == "Streaming response"
    
    def test_langchain_error_handling(self):
        """Test error handling with LangChain models"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Mock LLM that raises an error
            mock_llm = Mock()
            mock_llm.invoke.side_effect = Exception("LangChain model error")
            mock_llm.model_name = "error-model"
            
            ai = PersonalityAI(self.test_personality)
            ai.set_provider("langchain", llm=mock_llm)
            
            with pytest.raises(Exception, match="LangChain model error"):
                ai.chat("Test error")


@pytest.mark.integration 
class TestLangChainIntegration:
    """Integration tests for LangChain provider (requires actual models)"""
    
    def setup_method(self):
        """Setup for integration tests"""
        # Load environment variables from .env file in tests directory
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        load_dotenv(env_path)
        
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    def test_langchain_with_mock_models(self):
        """Test LangChain integration with comprehensive mock models"""
        # This test simulates real LangChain models without requiring API keys
        
        langchain_models = [
            ("ChatOpenAI", "gpt-4", "OpenAI response via LangChain"),
            ("ChatAnthropic", "claude-3-sonnet-20240229", "Anthropic response via LangChain"),
            ("Ollama", "llama2", "Local response via LangChain"),
            ("ChatGoogleGenerativeAI", "gemini-pro", "Google response via LangChain"),
            ("HuggingFaceEndpoint", "microsoft/DialoGPT-medium", "HuggingFace response via LangChain")
        ]
        
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            for class_name, model_name, expected_response in langchain_models:
                # Create mock LLM
                mock_llm = MockLangChainLLM(model_name, expected_response)
                mock_llm.__class__.__name__ = class_name
                
                # Test with different personalities
                for personality_name, personality_dsl in PERSONALITY_TEMPLATES.items():
                    ai = PersonalityAI(personality_dsl)
                    ai.set_provider("langchain", llm=mock_llm)
                    
                    # Test basic functionality
                    response = ai.chat(f"Test {personality_name}")
                    assert response == expected_response
                    
                    # Test provider info
                    info = ai.get_provider_info()
                    assert info["default_model"] == model_name
                    assert class_name.lower() in info["provider"]
                    
                    print(f"✅ {class_name} with {personality_name}: OK")
    
    def test_langchain_provider_switching(self):
        """Test switching between different LangChain models"""
        with patch('langchain_core.messages') as mock_messages:
            mock_messages.SystemMessage = Mock()
            mock_messages.HumanMessage = Mock()
            mock_messages.AIMessage = Mock()
            
            # Create AI instance
            ai = PersonalityAI(PERSONALITY_TEMPLATES["technical_mentor"])
            
            # Test switching between different mock LangChain models
            models = [
                MockLangChainLLM("gpt-4", "GPT-4 technical response"),
                MockLangChainLLM("claude-3", "Claude technical response"),
                MockLangChainLLM("llama2", "Llama technical response")
            ]
            
            for i, model in enumerate(models):
                ai.set_provider("langchain", llm=model)
                
                # Test that the provider switched correctly
                info = ai.get_provider_info()
                assert info["default_model"] == model.model_name
                
                # Test that personality remains consistent
                summary = ai.get_personality_summary()
                assert summary["name"] == "Technical Programming Mentor"
                
                # Test response
                response = ai.chat(f"Question {i+1}")
                assert model.model_name.replace("-", " ") in response.lower() or response.startswith(("GPT-4", "Claude", "Llama"))
                
                print(f"✅ Switched to {model.model_name}: {response}")
    
    def test_real_langchain_openai_integration(self):
        """Test real LangChain + OpenAI integration with different personalities"""
        if not self.openai_api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            pytest.skip("langchain-openai not installed")
        
        # Test different personalities with real OpenAI via LangChain
        personalities = [
            ("helpful_assistant", "I'm here to help!"),
            ("creative_writer", "creativity"),
            ("technical_mentor", "technical")
        ]
        
        for personality_name, expected_trait in personalities:
            personality_dsl = PERSONALITY_TEMPLATES[personality_name]
            
            # Create real LangChain OpenAI model
            llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                api_key=self.openai_api_key,
                max_tokens=50,
                temperature=0.3
            )
            
            # Use with PersonalityAI
            ai = PersonalityAI(personality_dsl)
            ai.set_provider("langchain", llm=llm)
            
            # Test basic functionality
            response = ai.chat(f"Say hello in the style of a {personality_name.replace('_', ' ')}")
            
            # Verify response
            assert isinstance(response, str)
            assert len(response.strip()) > 0
            
            # Check provider info
            info = ai.get_provider_info()
            assert "chatopenai" in info["provider"].lower()
            assert info["default_model"] == "gpt-3.5-turbo"
            
            print(f"✅ {personality_name} via LangChain+OpenAI: {response[:60]}...")
    
    def test_langchain_openai_personality_consistency(self):
        """Test that same personality produces consistent responses via LangChain"""
        if not self.openai_api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            pytest.skip("langchain-openai not installed")
        
        # Use technical mentor personality
        personality_dsl = PERSONALITY_TEMPLATES["technical_mentor"]
        
        # Create two identical LangChain models
        llm1 = ChatOpenAI(model="gpt-3.5-turbo", api_key=self.openai_api_key, max_tokens=30, temperature=0.1)
        llm2 = ChatOpenAI(model="gpt-3.5-turbo", api_key=self.openai_api_key, max_tokens=30, temperature=0.1)
        
        # Create two AI instances with same personality
        ai1 = PersonalityAI(personality_dsl)
        ai1.set_provider("langchain", llm=llm1)
        
        ai2 = PersonalityAI(personality_dsl)
        ai2.set_provider("langchain", llm=llm2)
        
        # Test same question to both
        question = "Explain programming in 5 words"
        response1 = ai1.chat(question)
        response2 = ai2.chat(question)
        
        # Both should respond (content may differ due to randomness, but should be technical)
        assert isinstance(response1, str) and len(response1.strip()) > 0
        assert isinstance(response2, str) and len(response2.strip()) > 0
        
        # Verify both use same personality
        summary1 = ai1.get_personality_summary()
        summary2 = ai2.get_personality_summary()
        assert summary1["name"] == summary2["name"] == "Technical Programming Mentor"
        
        print(f"✅ Response 1: {response1}")
        print(f"✅ Response 2: {response2}")
        print("✅ Same personality, consistent technical focus!")
    
    def test_langchain_openai_conversation_history(self):
        """Test conversation history with LangChain + OpenAI"""
        if not self.openai_api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            pytest.skip("langchain-openai not installed")
        
        # Create LangChain OpenAI model
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=self.openai_api_key,
            max_tokens=40,
            temperature=0.2
        )
        
        # Use creative writer personality
        ai = PersonalityAI(PERSONALITY_TEMPLATES["creative_writer"])
        ai.set_provider("langchain", llm=llm)
        
        # Start conversation with history
        response1 = ai.chat("I'm writing a story about robots", use_history=True)
        response2 = ai.chat("What was my story about?", use_history=True)
        
        # Check responses
        assert isinstance(response1, str) and len(response1.strip()) > 0
        assert isinstance(response2, str) and len(response2.strip()) > 0
        
        # Second response should reference robots/story from first message
        assert any(word in response2.lower() for word in ["robot", "story", "writing"]), \
               f"Expected reference to robots/story in: {response2}"
        
        # Check conversation history
        history = ai.get_conversation_history()
        assert len(history) == 4  # 2 user + 2 assistant messages
        assert "robots" in history[0]["content"]
        
        print(f"✅ First response: {response1}")
        print(f"✅ Second response: {response2}")
        print("✅ LangChain + OpenAI maintains conversation history!")
    
    def test_langchain_openai_multiple_models(self):
        """Test different OpenAI models via LangChain with same personality"""
        if not self.openai_api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            pytest.skip("langchain-openai not installed")
        
        # Test different models with same personality
        models = ["gpt-3.5-turbo", "gpt-4o-mini"]
        personality_dsl = PERSONALITY_TEMPLATES["helpful_assistant"]
        
        responses = {}
        for model_name in models:
            try:
                # Create LangChain model
                llm = ChatOpenAI(
                    model=model_name,
                    api_key=self.openai_api_key,
                    max_tokens=25,
                    temperature=0.3
                )
                
                # Use with same personality
                ai = PersonalityAI(personality_dsl)
                ai.set_provider("langchain", llm=llm)
                
                # Test
                response = ai.chat("Help me understand AI in one sentence")
                responses[model_name] = response
                
                # Verify provider info
                info = ai.get_provider_info()
                assert info["default_model"] == model_name
                
                print(f"✅ {model_name} via LangChain: {response}")
                
            except Exception as e:
                print(f"⚠️ {model_name} not available: {str(e)[:50]}")
                continue
        
        # Should have at least one successful response
        assert len(responses) > 0, "No models were successfully tested"
        
        # All responses should be helpful (from helpful_assistant personality)
        for model, response in responses.items():
            assert isinstance(response, str) and len(response.strip()) > 0
    
    def test_custom_colo_personality_with_langchain_openai(self):
        """Test custom .colo personality definition with LangChain + OpenAI"""
        if not self.openai_api_key:
            pytest.skip("OPENAI_API_KEY environment variable not set")
        
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            pytest.skip("langchain-openai not installed")
        
        # Define a custom personality in .colo format
        custom_personality = '''personality: "AI Code Reviewer"

traits:
  analytical_thinking: 0.95
  attention_to_detail: 0.90
  constructive_criticism: 0.85
  mentoring: 0.80
  
knowledge:
  domain software_engineering:
    code_review: expert
    best_practices: expert
    debugging: advanced
    optimization: advanced
  
behaviors:
  - when analytical_thinking > 0.9 → prefer "systematic analysis"
  - when attention_to_detail > 0.8 → seek "thorough examination"
  - when constructive_criticism > 0.8 → avoid "harsh criticism"
evolution:
  - learns "code_patterns" → analytical_thinking += 0.05'''
        
        # Create LangChain OpenAI model
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=self.openai_api_key,
            max_tokens=60,
            temperature=0.2
        )
        
        # Use custom personality
        ai = PersonalityAI(custom_personality)
        ai.set_provider("langchain", llm=llm)
        
        # Test code review scenario
        code_question = "Review this Python function: def calc(x): return x*2"
        response = ai.chat(code_question)
        
        # Verify response
        assert isinstance(response, str) and len(response.strip()) > 0
        
        # Check personality info
        summary = ai.get_personality_summary()
        assert summary["name"] == "AI Code Reviewer"
        assert "analytical_thinking" in summary["traits"]
        assert summary["traits"]["analytical_thinking"] == 0.95
        
        # Response should be analytical and constructive
        response_lower = response.lower()
        analytical_words = ["function", "code", "improve", "consider", "suggest", "analysis"]
        assert any(word in response_lower for word in analytical_words), \
               f"Expected analytical response, got: {response}"
        
        print(f"✅ Custom personality: AI Code Reviewer")
        print(f"✅ LangChain + OpenAI response: {response}")
        print("✅ Custom .colo personality works perfectly via LangChain!")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
