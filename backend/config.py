"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    # LLM (OpenAI-compatible)
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "sk-placeholder"
    llm_model_name: str = "gpt-4o"

    # File storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 50

    # Session
    session_ttl_hours: int = 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
