import sys
from pathlib import Path
from unittest.mock import patch

from aicm.config import DEFAULTS, MODEL_DEFAULTS, get_config, load_config, save_config


def test_defaults():
    assert DEFAULTS["backend"] == "ollama"
    assert DEFAULTS["format"] == "conventional"
    assert DEFAULTS["ollama_url"] == "http://localhost:11434"


def test_load_config_missing_file(tmp_path):
    with patch("aicm.config.CONFIG_PATH", tmp_path / "missing.toml"):
        assert load_config() == {}


def test_save_and_load_config(tmp_path):
    config_path = tmp_path / "config.toml"
    with patch("aicm.config.CONFIG_PATH", config_path):
        save_config({"backend": "ollama", "model": "llama3.2"})
        assert config_path.exists()
        loaded = load_config()
        assert loaded["backend"] == "ollama"
        assert loaded["model"] == "llama3.2"


def test_save_config_skips_none(tmp_path):
    config_path = tmp_path / "config.toml"
    with patch("aicm.config.CONFIG_PATH", config_path):
        save_config({"backend": "ollama", "profile": None})
        content = config_path.read_text()
        assert "profile" not in content


def test_get_config_defaults(tmp_path):
    with patch("aicm.config.CONFIG_PATH", tmp_path / "missing.toml"):
        config = get_config()
        assert config["backend"] == "ollama"
        assert config["model"] == MODEL_DEFAULTS["ollama"]
        assert config["format"] == "conventional"


def test_get_config_cli_overrides(tmp_path):
    with patch("aicm.config.CONFIG_PATH", tmp_path / "missing.toml"):
        config = get_config({"backend": "ollama", "model": None})
        assert config["backend"] == "ollama"
        assert config["model"] == MODEL_DEFAULTS["ollama"]


def test_get_config_file_overrides(tmp_path):
    config_path = tmp_path / "config.toml"
    with patch("aicm.config.CONFIG_PATH", config_path):
        save_config({"backend": "ollama", "model": "codellama"})
        config = get_config()
        assert config["backend"] == "ollama"
        assert config["model"] == "codellama"


def test_get_config_cli_beats_file(tmp_path):
    config_path = tmp_path / "config.toml"
    with patch("aicm.config.CONFIG_PATH", config_path):
        save_config({"backend": "ollama", "model": "llama3.2"})
        config = get_config({"model": "codellama"})
        assert config["model"] == "codellama"
