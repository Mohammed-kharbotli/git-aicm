import re
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".aicm.toml"
PROJECT_CONFIG_NAME = ".aicm.toml"

VALID_KEYS = {
    "backend", "model", "ollama_url", "profile", "format",
    "anthropic_api_key", "ticket",
}

VALID_BACKENDS = {"ollama", "bedrock", "anthropic"}
VALID_FORMATS = {"conventional", "simple"}

DEFAULTS = {
    "backend": "ollama",
    "model": None,
    "ollama_url": "http://localhost:11434",
    "profile": None,
    "format": "conventional",
}

MODEL_DEFAULTS = {
    "bedrock": "eu.anthropic.claude-sonnet-4-20250514-v1:0",
    "ollama": "qwen2.5-coder:7b",
    "anthropic": "claude-sonnet-4-20250514",
}

BACKEND_DEPS = {
    "bedrock": "boto3",
    "anthropic": "anthropic",
}

_TICKET_RE = re.compile(r"[A-Z][A-Z0-9]+-\d+")


def validate_config_value(key, value):
    if key not in VALID_KEYS:
        return f"Invalid config key: {key}. Valid keys: {', '.join(sorted(VALID_KEYS))}"
    if not isinstance(value, str) or not value.strip():
        return f"Value for '{key}' must be a non-empty string"
    if len(value) > 500:
        return f"Value for '{key}' is too long (max 500 chars)"
    if key == "backend" and value not in VALID_BACKENDS:
        return f"Invalid backend: {value}. Use: {', '.join(sorted(VALID_BACKENDS))}"
    if key == "format" and value not in VALID_FORMATS:
        return f"Invalid format: {value}. Use: {', '.join(sorted(VALID_FORMATS))}"
    if key == "ollama_url" and not value.startswith(("http://", "https://")):
        return f"Invalid URL: {value}. Must start with http:// or https://"
    if key == "model" and not re.match(r'^[a-zA-Z0-9._:/-]+$', value):
        return f"Invalid model name: {value}. Only alphanumeric, dots, colons, slashes, hyphens allowed"
    if key == "profile" and not re.match(r'^[a-zA-Z0-9_-]+$', value):
        return f"Invalid profile name: {value}. Only alphanumeric, hyphens, underscores allowed"
    if key == "anthropic_api_key" and not re.match(r'^sk-ant-[a-zA-Z0-9_-]+$', value):
        return "Invalid API key format. Anthropic keys start with 'sk-ant-'"
    if key == "ticket" and not _TICKET_RE.fullmatch(value):
        return f"Invalid ticket format: {value}. Expected: PROJ-123"
    return None


def _load_toml(path):
    if not path.exists():
        return {}
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        filtered = {}
        for k, v in data.items():
            if k not in VALID_KEYS:
                continue
            if validate_config_value(k, v) is None:
                filtered[k] = v
        return filtered
    except Exception:
        return {}


def _get_project_root():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def load_config():
    return _load_toml(CONFIG_PATH)


def load_project_config():
    root = _get_project_root()
    if not root:
        return {}
    return _load_toml(root / PROJECT_CONFIG_NAME)


def save_config(config, project=False):
    if project:
        root = _get_project_root()
        if not root:
            from aicm.utils import err
            err("Not a git repository. Cannot create project config.")
        path = root / PROJECT_CONFIG_NAME
    else:
        path = CONFIG_PATH
    lines = []
    for k, v in config.items():
        if v is not None:
            escaped = str(v).replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'{k} = "{escaped}"')
    try:
        path.write_text("\n".join(lines) + "\n")
        import os
        os.chmod(path, 0o600)
    except OSError as e:
        from aicm.utils import err
        err(f"Cannot write config to {path}: {e}")


def get_config(cli_overrides=None):
    config = {**DEFAULTS, **load_config(), **load_project_config()}
    if cli_overrides:
        config.update({k: v for k, v in cli_overrides.items() if v is not None})
    if not config.get("model"):
        config["model"] = MODEL_DEFAULTS.get(config["backend"], "")
    return config
