import sys
from pathlib import Path
from unittest.mock import patch

from aicm.config import DEFAULTS, MODEL_DEFAULTS, VALID_KEYS, get_config, load_config, save_config, validate_config_value


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


def test_save_config_escapes_special_chars(tmp_path):
    config_path = tmp_path / "config.toml"
    with patch("aicm.config.CONFIG_PATH", config_path):
        save_config({"ollama_url": 'http://host/path?a=1&b="2"'})
        loaded = load_config()
        assert loaded["ollama_url"] == 'http://host/path?a=1&b="2"'


def test_save_config_escapes_backslashes(tmp_path):
    config_path = tmp_path / "config.toml"
    with patch("aicm.config.CONFIG_PATH", config_path):
        save_config({"ollama_url": 'http://host/path?a="1"'})
        loaded = load_config()
        assert loaded["ollama_url"] == 'http://host/path?a="1"'


def test_validate_config_value_invalid_key():
    assert validate_config_value("foo", "bar") is not None
    assert "Invalid config key" in validate_config_value("foo", "bar")


def test_validate_config_value_empty():
    assert validate_config_value("backend", "") is not None
    assert validate_config_value("backend", "   ") is not None


def test_validate_config_value_too_long():
    assert validate_config_value("model", "a" * 501) is not None


def test_validate_config_value_backend():
    assert validate_config_value("backend", "ollama") is None
    assert validate_config_value("backend", "bedrock") is None
    assert validate_config_value("backend", "invalid") is not None


def test_validate_config_value_format():
    assert validate_config_value("format", "conventional") is None
    assert validate_config_value("format", "simple") is None
    assert validate_config_value("format", "fancy") is not None


def test_validate_config_value_ollama_url():
    assert validate_config_value("ollama_url", "http://localhost:11434") is None
    assert validate_config_value("ollama_url", "https://my-server.com") is None
    assert validate_config_value("ollama_url", "ftp://bad") is not None


def test_validate_config_value_model():
    assert validate_config_value("model", "qwen2.5-coder:7b") is None
    assert validate_config_value("model", "eu.anthropic.claude-sonnet-4-20250514-v1:0") is None
    assert validate_config_value("model", "model with spaces") is not None
    assert validate_config_value("model", "model;injection") is not None


def test_validate_config_value_profile():
    assert validate_config_value("profile", "my-profile") is None
    assert validate_config_value("profile", "dev_account") is None
    assert validate_config_value("profile", "has spaces") is not None


def test_validate_config_value_ticket():
    assert validate_config_value("ticket", "PROJ-123") is None
    assert validate_config_value("ticket", "proj-123") is not None
    assert validate_config_value("ticket", "PROJ-123-extra") is not None


def test_validate_config_value_api_key():
    assert validate_config_value("anthropic_api_key", "sk-ant-abc123def456ghij7890") is None
    assert validate_config_value("anthropic_api_key", "bad-key") is not None


def test_load_config_filters_invalid_keys(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text('backend = "ollama"\ninvalid_key = "junk"\n')
    with patch("aicm.config.CONFIG_PATH", config_path):
        loaded = load_config()
        assert "backend" in loaded
        assert "invalid_key" not in loaded
