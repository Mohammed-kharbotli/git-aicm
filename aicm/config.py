import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path.home() / ".aicm.toml"
PROJECT_CONFIG_NAME = ".aicm.toml"

DEFAULTS = {
    "backend": "ollama",
    "model": None,
    "ollama_url": "http://localhost:11434",
    "profile": None,
    "format": "conventional",
}

MODEL_DEFAULTS = {
    "bedrock": "eu.anthropic.claude-sonnet-4-20250514-v1:0",
    "ollama": "llama3.2",
    "anthropic": "claude-sonnet-4-20250514",
}

BACKEND_DEPS = {
    "bedrock": "boto3",
    "anthropic": "anthropic",
}


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
            return tomllib.load(f)
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
            lines.append(f'{k} = "{v}"')
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
