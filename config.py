"""
Configuration management for PolyMind Core.
Handles environment variables and API keys.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    solana_rpc_url: str = Field(
        default="https://api.mainnet-beta.solana.com",
        env="SOLANA_RPC_URL"
    )
    solana_ws_url: str = Field(
        default="wss://api.mainnet-beta.solana.com",
        env="SOLANA_WS_URL"
    )
    
    # Model Configuration
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    # Server Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

