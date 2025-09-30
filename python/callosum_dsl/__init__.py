"""
Callosum Personality DSL - Python Package

A powerful Python wrapper for the Callosum Personality Domain Specific Language.
Create rich, dynamic AI personalities with traits, knowledge domains, behaviors, and evolution patterns.

Example:
    >>> from callosum_dsl import Callosum, PERSONALITY_TEMPLATES
    >>> callosum = Callosum()
    >>> personality = callosum.to_json(PERSONALITY_TEMPLATES["helpful_assistant"])
    >>> print(f"Created: {personality['name']}")

For more examples and documentation, visit: https://github.com/your-repo/callosum
"""

from .core import (
    Callosum, 
    PersonalityAI, 
    CallosumError, 
    ParseError, 
    CompileError,
    OpenAIProvider,
    AnthropicProvider, 
    LangChainProvider,
    GenericProvider,
    create_provider,
    auto_detect_providers
)
from .templates import PERSONALITY_TEMPLATES

__version__ = "0.1.0"
__author__ = "Callosum Team"
__email__ = "contact@callosum.ai"

__all__ = [
    "Callosum",
    "PersonalityAI", 
    "CallosumError",
    "ParseError",
    "CompileError",
    "PERSONALITY_TEMPLATES",
    "OpenAIProvider",
    "AnthropicProvider",
    "LangChainProvider", 
    "GenericProvider",
    "create_provider",
    "auto_detect_providers"
]
