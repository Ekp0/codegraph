"""
CodeGraph Backend - Anthropic LLM Provider
"""
from typing import AsyncGenerator
import logging

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from app.llm.base import (
    BaseLLMProvider,
    Message,
    MessageRole,
    LLMResponse,
    StreamChunk,
)
from app.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""
    
    provider_name = "anthropic"
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs
    ):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or settings.anthropic_api_key
        
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("anthropic package not installed")
        
        self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    @property
    def default_model(self) -> str:
        return "claude-3-sonnet-20240229"
    
    @property
    def available_models(self) -> list[str]:
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
        ]
    
    def format_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Format messages for Anthropic API (separate system message)."""
        system_message = None
        formatted = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system_message = msg.content
            else:
                formatted.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })
        
        return system_message, formatted
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion from a prompt."""
        messages = [Message(role=MessageRole.USER, content=prompt)]
        return await self.chat(messages, max_tokens, temperature, **kwargs)
    
    async def chat(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a chat completion."""
        system_message, formatted = self.format_messages(messages)
        
        create_kwargs = {
            "model": self.model,
            "messages": formatted,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_message:
            create_kwargs["system"] = system_message
        
        response = await self._client.messages.create(**create_kwargs)
        
        content = ""
        if response.content:
            content = response.content[0].text
        
        return LLMResponse(
            content=content,
            model=response.model,
            finish_reason=response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            raw_response=response,
        )
    
    async def stream_chat(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a chat completion."""
        system_message, formatted = self.format_messages(messages)
        
        create_kwargs = {
            "model": self.model,
            "messages": formatted,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if system_message:
            create_kwargs["system"] = system_message
        
        async with self._client.messages.stream(**create_kwargs) as stream:
            async for text in stream.text_stream:
                yield StreamChunk(content=text, is_final=False)
        
        yield StreamChunk(content="", is_final=True)
