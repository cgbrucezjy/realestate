"""
Configuration management for the KAG system.

This module handles loading and managing configuration for the KAG system.
It supports loading from environment variables and configuration files.
"""

import os
import json
from typing import Dict, List, Optional, Any
from functools import lru_cache

from pydantic import BaseModel, Field

class Settings(BaseModel):
    """Settings for the KAG system."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="KAG_HOST")
    port: int = Field(default=11434, env="KAG_PORT")
    
    # Model settings
    model_path: str = Field(default="./qwq", env="KAG_MODEL_PATH")
    tensor_parallel_size: int = Field(default=2, env="KAG_TENSOR_PARALLEL_SIZE")
    gpu_memory_utilization: float = Field(default=0.7, env="KAG_GPU_MEMORY_UTILIZATION")
    max_model_len: int = Field(default=4096, env="KAG_MAX_MODEL_LEN")
    disable_custom_all_reduce: bool = Field(default=True, env="KAG_DISABLE_CUSTOM_ALL_REDUCE")
    
    # KV cache settings
    kv_cache_token_limit: int = Field(default=8192, env="KAG_KV_CACHE_TOKEN_LIMIT")
    kv_cache_cleanup_interval: int = Field(default=3600, env="KAG_KV_CACHE_CLEANUP_INTERVAL")
    
    # Document processing settings
    chunk_size: int = Field(default=512, env="KAG_CHUNK_SIZE")
    chunk_overlap: int = Field(default=128, env="KAG_CHUNK_OVERLAP")
    
    # Session settings
    session_timeout: int = Field(default=86400, env="KAG_SESSION_TIMEOUT")  # 24 hours
    
    # Database settings
    database_url: str = Field(default="sqlite:///kag.db", env="KAG_DATABASE_URL")
    
    # Authentication settings
    auth_enabled: bool = Field(default=True, env="KAG_AUTH_ENABLED")
    jwt_secret: str = Field(default="your-secret-key", env="KAG_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="KAG_JWT_ALGORITHM")
    jwt_expires_minutes: int = Field(default=60 * 24, env="KAG_JWT_EXPIRES_MINUTES")  # 24 hours
    
    # Logging settings
    log_level: str = Field(default="INFO", env="KAG_LOG_LEVEL")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="KAG_LOG_FORMAT")
    
    # OpenAI API compatibility settings
    openai_api_prefix: str = Field(default="/v1", env="KAG_OPENAI_API_PREFIX")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "KAG_"
        case_sensitive = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return self.dict()
    
    def to_json(self) -> str:
        """Convert settings to JSON."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_config_file(cls, config_file: str) -> "Settings":
        """Load settings from configuration file."""
        if not os.path.exists(config_file):
            return cls()
        
        with open(config_file, "r") as f:
            config = json.load(f)
        
        return cls(**config)


@lru_cache()
def get_settings() -> Settings:
    """
    Get settings singleton.
    
    This function is cached so that only one instance of Settings is created.
    """
    config_file = os.environ.get("KAG_CONFIG_FILE", "config.json")
    if os.path.exists(config_file):
        return Settings.from_config_file(config_file)
    return Settings()


def make_default_config_file(path: str = "config.json") -> None:
    """
    Create a default configuration file.
    
    Args:
        path: Path to the configuration file
    """
    settings = Settings()
    with open(path, "w") as f:
        f.write(settings.to_json()) 