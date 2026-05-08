# To add a new backend:
# 1. Create a file in this directory (e.g. openai.py)
# 2. Define a generate(prompt, config) -> str function
# 3. Optionally define a setup(config) -> config function for the setup wizard
# 4. That's it — it gets auto-registered

import importlib
import pkgutil

BACKENDS = {}
SETUPS = {}

# Whitelist of allowed backend modules for security
ALLOWED_BACKENDS = {"bedrock", "ollama", "anthropic"}


def _validate_config(config, backend_name):
    """Validate configuration for a specific backend."""
    if not isinstance(config, dict):
        return False
    
    # Common required fields
    if "model" not in config or not config["model"]:
        return False
    
    # Backend-specific validation
    if backend_name == "ollama":
        return bool(config.get("ollama_url"))
    elif backend_name == "anthropic":
        return bool(config.get("anthropic_api_key") or
                    "ANTHROPIC_API_KEY" in __import__("os").environ)
    elif backend_name == "bedrock":
        return True  # AWS credentials validated elsewhere
    
    return True


def _make_validated_generate(backend_name, original_func):
    """Create a validated wrapper for generate function."""
    def validated_generate(prompt, config):
        if not _validate_config(config, backend_name):
            from aicm.utils import err
            err(f"Invalid configuration for {backend_name} backend")
        return original_func(prompt, config)
    return validated_generate


for _, name, _ in pkgutil.iter_modules(__path__):
    if name not in ALLOWED_BACKENDS:
        continue
    module = importlib.import_module(f"{__name__}.{name}")
    if hasattr(module, "generate"):
        # Wrap generate function with config validation
        BACKENDS[name] = _make_validated_generate(name, module.generate)
    if hasattr(module, "setup"):
        SETUPS[name] = module.setup
