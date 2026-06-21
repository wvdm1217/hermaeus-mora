from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchConfig(BaseSettings):
    enabled: bool = True
    vector_enabled: bool = False
    provider: str = "ollama"
    embedding_model: str = "embeddinggemma"

    model_config = SettingsConfigDict(
        env_prefix="hm_search_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    data_dir: Path = Path("data")
    search: SearchConfig = Field(default_factory=SearchConfig)

    model_config = SettingsConfigDict(
        env_prefix="hm_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
