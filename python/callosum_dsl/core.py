"""
Core classes and functions for Callosum Personality DSL Python integration
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Protocol
from abc import ABC, abstractmethod

# Handle resource loading with backwards compatibility
try:
    # Python 3.9+
    from importlib import resources
    def _get_resource_path(package: str, resource: str) -> str:
        # Handle subdirectories properly
        if '/' in resource:
            parts = resource.split('/')
            subpackage = '.'.join([package] + parts[:-1])
            filename = parts[-1]
            files = resources.files(subpackage)
            return str(files / filename)
        else:
            files = resources.files(package)
            return str(files / resource)
except ImportError:
    try:
        # Python 3.8 - try importlib_resources
        import importlib_resources as resources
        def _get_resource_path(package: str, resource: str) -> str:
            if '/' in resource:
                parts = resource.split('/')
                subpackage = '.'.join([package] + parts[:-1])
                filename = parts[-1]
                files = resources.files(subpackage)
                return str(files / filename)
            else:
                files = resources.files(package)
                return str(files / resource)
    except ImportError:
        # Fallback to pkg_resources (deprecated but available)
        import pkg_resources
        def _get_resource_path(package: str, resource: str) -> str:
            return pkg_resources.resource_filename(package, resource)


class CallosumError(Exception):
    """Base exception for Callosum DSL errors"""
    pass


class ParseError(CallosumError):
    """Raised when DSL parsing fails"""
    pass


class CompileError(CallosumError):
    """Raised when DSL compilation fails"""
    pass


# Provider-agnostic AI interface
class AIProvider(Protocol):
    """Protocol for AI provider implementations"""
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        """Send chat messages and return response"""
        pass
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Get default model for this provider"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name"""
        pass


class OpenAIProvider:
    """OpenAI provider implementation"""
    
    def __init__(self, api_key: str, **kwargs):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key, **kwargs)
        except ImportError:
            raise CallosumError(
                "OpenAI package not installed. Install with: pip install openai"
            )
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content
    
    @property
    def default_model(self) -> str:
        return "gpt-4"
    
    @property
    def provider_name(self) -> str:
        return "openai"


class AnthropicProvider:
    """Anthropic provider implementation"""
    
    def __init__(self, api_key: str, **kwargs):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key, **kwargs)
        except ImportError:
            raise CallosumError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        # Separate system message from other messages
        system_message = None
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)
        
        response = self.client.messages.create(
            model=model or self.default_model,
            max_tokens=kwargs.pop('max_tokens', 1000),
            system=system_message,
            messages=chat_messages,
            **kwargs
        )
        return response.content[0].text
    
    @property
    def default_model(self) -> str:
        return "claude-3-sonnet-20240229"
    
    @property
    def provider_name(self) -> str:
        return "anthropic"


class LangChainProvider:
    """LangChain provider implementation - works with any LangChain LLM"""
    
    def __init__(self, llm=None, **kwargs):
        """
        Initialize with a LangChain LLM instance
        
        Args:
            llm: Any LangChain LLM instance (ChatOpenAI, ChatAnthropic, etc.)
        """
        try:
            from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
            from langchain_core.language_models.chat_models import BaseChatModel
            self._SystemMessage = SystemMessage
            self._HumanMessage = HumanMessage
            self._AIMessage = AIMessage
        except ImportError:
            raise CallosumError(
                "LangChain not installed. Install with: pip install langchain-core"
            )
        
        if llm is None:
            raise ValueError("LangChain LLM instance is required")
        
        if not hasattr(llm, 'invoke'):
            raise ValueError("Provided LLM must have an 'invoke' method (LangChain compatible)")
        
        self.llm = llm
        self._model_name = getattr(llm, 'model_name', None) or getattr(llm, 'model', 'unknown')
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        # Convert dict messages to LangChain message objects
        langchain_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                langchain_messages.append(self._SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(self._HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(self._AIMessage(content=content))
            else:
                # Default to human message for unknown roles
                langchain_messages.append(self._HumanMessage(content=content))
        
        # Invoke the LLM
        response = self.llm.invoke(langchain_messages, **kwargs)
        
        # Handle different response types
        if hasattr(response, 'content'):
            return response.content
        elif isinstance(response, str):
            return response
        else:
            return str(response)
    
    @property
    def default_model(self) -> str:
        return self._model_name
    
    @property
    def provider_name(self) -> str:
        return f"langchain-{type(self.llm).__name__.lower()}"


class GenericProvider:
    """Generic provider for custom AI implementations"""
    
    def __init__(self, chat_function, model_name: str = "custom", provider_name: str = "generic", **kwargs):
        """
        Initialize with a custom chat function
        
        Args:
            chat_function: Function that takes (messages, model, **kwargs) and returns str
            model_name: Name of the model
            provider_name: Name of the provider
        """
        if not callable(chat_function):
            raise ValueError("chat_function must be callable")
        
        self._chat_function = chat_function
        self._model_name = model_name
        self._provider_name = provider_name
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, **kwargs) -> str:
        return self._chat_function(messages, model or self.default_model, **kwargs)
    
    @property
    def default_model(self) -> str:
        return self._model_name
    
    @property
    def provider_name(self) -> str:
        return self._provider_name


def create_provider(provider_type: str, **kwargs) -> AIProvider:
    """Factory function to create AI providers"""
    provider_type = provider_type.lower()
    
    if provider_type == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_type == "anthropic":
        return AnthropicProvider(**kwargs)
    elif provider_type == "langchain":
        return LangChainProvider(**kwargs)
    elif provider_type == "generic":
        return GenericProvider(**kwargs)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


def auto_detect_providers() -> List[str]:
    """Detect available AI providers based on installed packages"""
    available = []
    
    # Check OpenAI
    try:
        import openai
        available.append("openai")
    except ImportError:
        pass
    
    # Check Anthropic
    try:
        import anthropic
        available.append("anthropic")
    except ImportError:
        pass
    
    # Check LangChain
    try:
        from langchain_core.language_models.chat_models import BaseChatModel
        available.append("langchain")
    except ImportError:
        pass
    
    return available


class Callosum:
    """
    Python wrapper for Callosum Personality DSL
    
    Provides direct access to the DSL compiler with a clean Python API.
    """
    
    def __init__(self, compiler_path: Optional[str] = None):
        """
        Initialize the Callosum wrapper
        
        Args:
            compiler_path: Path to the dsl-parser binary. If None, will search
                          for it in the package or system PATH
        """
        self.compiler_path = self._find_compiler(compiler_path)
        if not self.compiler_path:
            raise CallosumError(
                "DSL compiler not found. The binary should be included with the package. "
                "If you built from source, ensure 'dune build' was run."
            )
    
    def _find_compiler(self, explicit_path: Optional[str]) -> Optional[str]:
        """Find the DSL compiler binary"""
        if explicit_path:
            return explicit_path if os.path.exists(explicit_path) else None
            
        # Search in package resources first
        try:
            binary_path = _get_resource_path('callosum_dsl', 'bin/dsl-parser')
            if os.path.exists(binary_path) and os.access(binary_path, os.X_OK):
                return binary_path
        except:
            pass
            
        # Search in common development locations
        search_paths = [
            # In the project (for development) - new structure
            "core/_build/default/bin/main.exe",
            "core/_build/install/default/bin/dsl-parser",
            # Try from parent directory (when running from python/)
            "../core/_build/default/bin/main.exe", 
            "../core/_build/install/default/bin/dsl-parser",
            # Legacy paths for backward compatibility
            "personality/dsl/_build/default/bin/main.exe",
            "_build/default/bin/main.exe",
            # Installed system-wide
            "dsl-parser"
        ]
        
        for path in search_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                return abs_path
            
            # Check if it's in PATH
            if path == "dsl-parser":
                try:
                    result = subprocess.run(
                        ["which", "dsl-parser"], 
                        capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        return result.stdout.strip()
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
        
        return None
    
    def compile(self, dsl_content: str, target: str = "json", 
                context: Optional[str] = None) -> str:
        """
        Compile DSL content to target format
        
        Args:
            dsl_content: The personality DSL as string
            target: Output format (json, prompt, lua, sql, cypher)
            context: Optional context hint for prompt generation
            
        Returns:
            Compiled output as string
            
        Raises:
            ParseError: If DSL parsing fails
            CompileError: If compilation fails
        """
        if not dsl_content.strip():
            raise ParseError("DSL content is empty")
        
        # Prepare command
        cmd = [self.compiler_path, "--output", target]
        
        if context:
            cmd.extend(["--context", context])
        
        # Use stdin for DSL content
        cmd.extend(["--input", "-"])
        
        try:
            result = subprocess.run(
                cmd,
                input=dsl_content,
                capture_output=True,
                text=True,
                timeout=30  # Reasonable timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown compilation error"
                if "Parse errors:" in error_msg:
                    raise ParseError(error_msg)
                else:
                    raise CompileError(error_msg)
            
            # Filter out warnings from stdout (they start with "WARNING:")
            output_lines = result.stdout.split('\n')
            clean_output = '\n'.join(line for line in output_lines if not line.startswith('WARNING:'))
            
            return clean_output.strip()
            
        except subprocess.TimeoutExpired:
            raise CompileError("Compilation timed out")
        except FileNotFoundError:
            raise CallosumError(f"Compiler not found at: {self.compiler_path}")
    
    def to_json(self, dsl_content: str) -> Dict[str, Any]:
        """
        Compile DSL to JSON and return parsed data
        
        Args:
            dsl_content: The personality DSL as string
            
        Returns:
            Parsed personality data as dict
        """
        json_output = self.compile(dsl_content, "json")
        try:
            return json.loads(json_output)
        except json.JSONDecodeError as e:
            raise CompileError(f"Invalid JSON output: {e}")
    
    def to_prompt(self, dsl_content: str, context: Optional[str] = None) -> str:
        """
        Compile DSL to system prompt for LLMs
        
        Args:
            dsl_content: The personality DSL as string
            context: Optional context for prompt customization
            
        Returns:
            System prompt as string
        """
        return self.compile(dsl_content, "prompt", context)
    
    def to_lua(self, dsl_content: str) -> str:
        """
        Compile DSL to Lua script
        
        Args:
            dsl_content: The personality DSL as string
            
        Returns:
            Lua script as string
        """
        return self.compile(dsl_content, "lua")
    
    def to_sql(self, dsl_content: str) -> str:
        """
        Compile DSL to SQL schema and data
        
        Args:
            dsl_content: The personality DSL as string
            
        Returns:
            SQL statements as string
        """
        return self.compile(dsl_content, "sql")
    
    def to_cypher(self, dsl_content: str) -> str:
        """
        Compile DSL to Cypher queries for Neo4j
        
        Args:
            dsl_content: The personality DSL as string
            
        Returns:
            Cypher queries as string
        """
        return self.compile(dsl_content, "cypher")
    
    def load_file(self, filepath: Union[str, Path]) -> str:
        """
        Load DSL content from file
        
        Args:
            filepath: Path to .colo file
            
        Returns:
            DSL content as string
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise CallosumError(f"Failed to read file {filepath}: {e}")
    
    def validate(self, dsl_content: str) -> bool:
        """
        Validate DSL content without compilation
        
        Args:
            dsl_content: The personality DSL as string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.compile(dsl_content, "json")
            return True
        except (ParseError, CompileError):
            return False


class PersonalityAI:
    """
    Provider-agnostic AI assistant with Callosum personality
    
    Works with OpenAI, Anthropic, LangChain, and custom AI providers.
    """
    
    def __init__(self, personality_dsl: str, 
                 provider: Optional[Union[str, AIProvider]] = None,
                 compiler_path: Optional[str] = None,
                 **provider_kwargs):
        """
        Initialize AI with personality
        
        Args:
            personality_dsl: DSL defining the personality
            provider: Either:
                - String: "openai", "anthropic", "langchain", "generic" 
                - AIProvider instance for custom providers
                - None: Auto-detect based on available packages
            compiler_path: Path to DSL compiler
            **provider_kwargs: Arguments for provider initialization:
                - For OpenAI/Anthropic: api_key, base_url, etc.
                - For LangChain: llm (required), any other params
                - For Generic: chat_function (required), model_name, provider_name
        """
        self.callosum = Callosum(compiler_path)
        self.personality_dsl = personality_dsl
        
        # Compile personality
        try:
            self.personality_data = self.callosum.to_json(personality_dsl)
            self.system_prompt = self.callosum.to_prompt(personality_dsl)
        except (ParseError, CompileError) as e:
            raise CallosumError(f"Failed to compile personality: {e}")
        
        # Initialize AI provider
        self.ai_provider = self._init_provider(provider, **provider_kwargs)
        self.conversation_history = []  # Track conversation for multi-turn support
    
    def _init_provider(self, provider: Optional[Union[str, AIProvider]], **provider_kwargs) -> Optional[AIProvider]:
        """Initialize the AI provider"""
        # If provider is already an AIProvider instance
        if hasattr(provider, 'chat'):
            return provider
        
        # If no provider specified, try to auto-detect
        if provider is None:
            available = auto_detect_providers()
            if not available:
                return None  # No providers available
            provider = available[0]  # Use first available
        
        # Create provider from string
        if isinstance(provider, str):
            try:
                return create_provider(provider, **provider_kwargs)
            except Exception as e:
                if provider_kwargs:  # If kwargs were provided, this was intentional
                    raise CallosumError(f"Failed to initialize {provider} provider: {e}")
                else:  # No kwargs, return None for lazy initialization
                    return None
        
        raise ValueError(f"Invalid provider type: {type(provider)}")
    
    def set_provider(self, provider: Union[str, AIProvider], **provider_kwargs):
        """
        Set or change the AI provider
        
        Args:
            provider: Provider type string or AIProvider instance
            **provider_kwargs: Provider initialization arguments
        """
        self.ai_provider = self._init_provider(provider, **provider_kwargs)
        if self.ai_provider is None:
            raise CallosumError("Failed to initialize provider")
    
    def chat(self, message: str, model: Optional[str] = None, 
             use_history: bool = False, reset_history: bool = False, **kwargs) -> str:
        """
        Chat with the AI using the personality
        
        Args:
            message: User message
            model: AI model to use (provider-specific)
            use_history: Whether to include conversation history
            reset_history: Whether to clear conversation history before this message
            **kwargs: Additional parameters for the AI provider
            
        Returns:
            AI response as string
        """
        if not self.ai_provider:
            raise CallosumError(
                "No AI provider initialized. Set provider using set_provider() method."
            )
        
        if reset_history:
            self.conversation_history = []
        
        # Build messages list
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history if requested
        if use_history:
            messages.extend(self.conversation_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Get response from provider
        response = self.ai_provider.chat(messages, model, **kwargs)
        
        # Update conversation history
        if use_history:
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": response})
        
        return response
    
    def chat_stream(self, message: str, model: Optional[str] = None, **kwargs):
        """
        Stream chat response (if provider supports it)
        
        Note: This is a placeholder for streaming functionality.
        Individual providers need to implement streaming support.
        """
        # For now, fall back to regular chat
        return self.chat(message, model, **kwargs)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        return auto_detect_providers()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider"""
        if not self.ai_provider:
            return {"provider": None, "default_model": None, "has_provider": False}
        
        return {
            "provider": self.ai_provider.provider_name,
            "default_model": self.ai_provider.default_model,
            "has_provider": True
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()
    
    def get_trait_strength(self, trait_name: str) -> Optional[float]:
        """Get the strength of a specific trait"""
        for trait in self.personality_data.get("traits", []):
            if trait["name"] == trait_name:
                return trait["strength"]
        return None
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get a summary of the personality"""
        traits = {trait["name"]: trait["strength"] 
                 for trait in self.personality_data.get("traits", [])}
        
        provider_info = self.get_provider_info()
        
        return {
            "name": self.personality_data.get("name"),
            "traits": traits,
            "dominant_trait": max(traits.keys(), key=lambda k: traits[k]) if traits else None,
            "knowledge_domains": [domain["name"] for domain in self.personality_data.get("knowledge", [])],
            "system_prompt_length": len(self.system_prompt),
            "provider": provider_info["provider"],
            "default_model": provider_info["default_model"],
            "conversation_length": len(self.conversation_history)
        }
