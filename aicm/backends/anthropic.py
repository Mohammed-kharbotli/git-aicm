import os

from aicm.utils import err


def generate(prompt, config):
    try:
        import anthropic
    except ImportError:
        err("anthropic not installed. Run: git-aicm reinstall, then pip install anthropic in the venv")
    api_key = config.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        err("No API key. Set ANTHROPIC_API_KEY env var or add anthropic_api_key to ~/.aicm.toml")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = []
        with client.messages.stream(
            model=config["model"],
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                message.append(text)
        print()
        return "".join(message)
    except Exception as e:
        estr = str(e)
        if "authentication" in estr.lower() or "api key" in estr.lower():
            err("Invalid Anthropic API key. Check your ANTHROPIC_API_KEY.")
        err(f"Anthropic error: {e}")


def setup(config):
    import re
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        print("\nANTHROPIC_API_KEY found in environment.")
        # Test the key by making a simple API call
        if _validate_api_key(api_key):
            print("API key validated successfully.")
        else:
            err("API key validation failed. Check your ANTHROPIC_API_KEY.")
    else:
        api_key = input("\nAnthropic API key: ").strip()
        if api_key:
            # Basic validation - Anthropic keys start with 'sk-ant-'
            if not re.match(r'^sk-ant-[a-zA-Z0-9_-]+$', api_key):
                err("Invalid API key format. Anthropic keys start with 'sk-ant-'")
            
            # Test the key
            if _validate_api_key(api_key):
                config["anthropic_api_key"] = api_key
                print("API key validated and saved.")
            else:
                err("API key validation failed. Check your key and try again.")
        else:
            err("API key required. Get one at https://console.anthropic.com/")
    return config


def _validate_api_key(api_key):
    """Validate API key by making a test request to Anthropic."""
    import re
    
    # Basic format validation first
    if not re.match(r'^sk-ant-[a-zA-Z0-9_-]{20,}$', api_key):
        return False
        
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        # Make a minimal test request
        client.messages.create(
            model="claude-3-haiku-20240307",  # Use cheapest model for validation
            max_tokens=1,
            messages=[{"role": "user", "content": "test"}]
        )
        return True
    except anthropic.AuthenticationError:
        return False
    except Exception:
        # For other errors (network, etc.), assume key format is valid
        # but we can't verify connectivity
        return True
