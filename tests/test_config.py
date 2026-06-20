from pathlib import Path

from hermaeus_mora.config import Settings


def test_config_default():
    settings = Settings()
    assert settings.data_dir == Path("data")


def test_config_env_override(monkeypatch):
    monkeypatch.setenv("HM_DATA_DIR", "/tmp/custom_data")
    settings = Settings()
    assert settings.data_dir == Path("/tmp/custom_data")
