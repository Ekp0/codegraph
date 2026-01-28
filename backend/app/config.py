"""
CodeGraph Backend - Configuration Settings
"""
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "CodeGraph"
    debug: bool = True
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Database
    database_url: str = Field(
        default="postgresql://codegraph:codegraph@localhost:5432/codegraph"
    )
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # LLM Providers
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    groq_api_key: str | None = None
    google_api_key: str | None = None
    cohere_api_key: str | None = None
    together_api_key: str | None = None
    openrouter_api_key: str | None = None
    
    # Default LLM Configuration
    default_llm_provider: Literal[
        "openai", "anthropic", "groq", "google", "cohere", "together", "openrouter"
    ] = "openai"
    default_llm_model: str = "gpt-4-turbo-preview"
    
    # Repository settings
    repos_dir: str = "/app/repos"
    max_repo_size_mb: int = 500
    
    # Embedding settings
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "/app/data/chroma"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def get_available_providers(self) -> list[str]:
        """Return list of configured LLM providers."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.groq_api_key:
            providers.append("groq")
        if self.google_api_key:
            providers.append("google")
        if self.cohere_api_key:
            providers.append("cohere")
        if self.together_api_key:
            providers.append("together")
        if self.openrouter_api_key:
            providers.append("openrouter")
        return providers
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
