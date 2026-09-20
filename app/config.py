"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("llm_api_key", "LLM_API_KEY", "api_key", "API_KEY"),
        description="LLM provider API key",
    )
    model_name: str = Field(
        default="gemini-3.1-flash-lite",
        validation_alias=AliasChoices("model_name", "MODEL_NAME", "llm_model_name", "LLM_MODEL_NAME"),
        description="Model name to use for recommendations",
    )
    max_sessions: int = Field(
        default=1000,
        validation_alias=AliasChoices("max_sessions", "MAX_SESSIONS"),
        description="Maximum number of active sessions to retain in memory before eviction",
    )
    whisper_model_size: str = Field(
        default="small",
        validation_alias=AliasChoices("whisper_model_size", "WHISPER_MODEL_SIZE"),
        description="faster-whisper model size name (e.g. small, base, tiny)",
    )
    whisper_device: str = Field(
        default="cpu",
        validation_alias=AliasChoices("whisper_device", "WHISPER_DEVICE"),
        description="Device for faster-whisper (cpu or cuda)",
    )
    whisper_compute_type: str = Field(
        default="int8",
        validation_alias=AliasChoices("whisper_compute_type", "WHISPER_COMPUTE_TYPE"),
        description="Compute type for faster-whisper (int8, float32, float16)",
    )
    cors_origins: List[str] = ["http://localhost:5173"]

    @property
    def llm_model_name(self) -> str:
        """Convenience alias for model_name."""
        return self.model_name


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
