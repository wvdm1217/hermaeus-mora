from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class SearchConfig(BaseModel):
    enabled: bool = True
    vector_enabled: bool = False
    provider: str = "ollama"
    embedding_model: str = "embeddinggemma"


class Settings(BaseSettings):
    data_dir: Path = Path("data")
    search: SearchConfig = SearchConfig()

    model_config = SettingsConfigDict(
        env_prefix="hm_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


settings = Settings()
