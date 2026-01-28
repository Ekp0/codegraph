"""
CodeGraph Backend - Groq LLM Provider
"""
from typing import AsyncGenerator
import logging

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from app.llm.base import (
    BaseLLMProvider,
    Message,
    LLMResponse,
    StreamChunk,
)
from app.config import settings

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider for fast inference."""
    
    provider_name = "groq"
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        **kwargs
    ):
        super().__init__(api_key, model, **kwargs)
        self.api_key = api_key or settings.groq_api_key
        
        if not GROQ_AVAILABLE:
            raise RuntimeError("groq package not installed")
        
        self._client = AsyncGroq(api_key=self.api_key)
    
    @property
    def default_model(self) -> str:
        return "llama-3.1-70b-versatile"
    
    @property
    def available_models(self) -> list[str]:
        return [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion from a prompt."""
        messages = [Message(role="user", content=prompt)]
        return await self.chat(messages, max_tokens, temperature, **kwargs)
    
    async def chat(
        self,
        messages: list[Message],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """Generate a chat completion."""
        formatted = self.format_messages(messages)
        
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=formatted,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        choice = response.choices[0]
        
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            finish_reason=choice.finish_reason,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
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
        formatted = self.format_messages(messages)
        
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=formatted,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield StreamChunk(
                    content=chunk.choices[0].delta.content,
                    is_final=chunk.choices[0].finish_reason is not None,
                )
