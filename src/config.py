"""Runtime configuration loaded from environment variables."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Relative paths are resolved from project root."""

    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    database_path: str = "data/fact_layer.db"
    max_pages_per_document: int = 150
    chunk_size: int = 3500
    chunk_overlap: int = 250
    low_confidence_threshold: float = 0.60
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def database_file(self, root: Path) -> Path:
        return root / self.database_path


settings = Settings()

