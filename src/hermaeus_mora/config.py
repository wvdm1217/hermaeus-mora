from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    data_dir: Path = Path("data")

    model_config = SettingsConfigDict(
        env_prefix="hm_", env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()
