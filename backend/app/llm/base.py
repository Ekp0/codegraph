"""
CodeGraph Backend - Abstract LLM Provider Base
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, Any
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """A chat message."""
    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    finish_reason: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    raw_response: Any = None


@dataclass
class StreamChunk:
    """A chunk of streamed response."""
    content: str
    is_final: bool = False


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    provider_name: str = "base"
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs
    ):
        self.api_key = api_key
        self.model = model or self.default_model
        self.kwargs = kwargs
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model for this provider."""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> list[str]:
        """List of available models."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion from a prompt."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a chat completion."""
        pass
    
    async def stream_chat(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a chat completion. Default implementation calls chat and yields full response."""
        response = await self.chat(messages, max_tokens, temperature, **kwargs)
        yield StreamChunk(content=response.content, is_final=True)
    
    def format_messages(self, messages: list[Message]) -> list[dict]:
        """Format messages for the provider's API."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count. Override for accurate counting."""
        # Rough estimate: ~4 chars per token
        return len(text) // 4
    
    def __repr__(self):
        return f"{self.__class__.__name__}(model={self.model})"
