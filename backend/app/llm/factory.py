"""
CodeGraph Backend - LLM Provider Factory
"""
from app.llm.base import BaseLLMProvider
from app.config import settings


def get_provider(
    provider_name: str | None = None,
    model: str | None = None,
    **kwargs
) -> BaseLLMProvider:
    """Factory function to get an LLM provider instance."""
    
    provider_name = provider_name or settings.default_llm_provider
    
    if provider_name == "openai":
        from app.llm.openai import OpenAIProvider
        return OpenAIProvider(model=model, **kwargs)
    
    elif provider_name == "anthropic":
        from app.llm.anthropic import AnthropicProvider
        return AnthropicProvider(model=model, **kwargs)
    
    elif provider_name == "groq":
        from app.llm.groq import GroqProvider
        return GroqProvider(model=model, **kwargs)
    
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def list_providers() -> list[str]:
    """List available LLM providers based on configured API keys."""
    return settings.get_available_providers()


def get_default_provider() -> BaseLLMProvider:
    """Get the default LLM provider."""
    return get_provider()
