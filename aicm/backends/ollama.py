import json
import urllib.request
import urllib.error

from aicm.utils import err


def generate(prompt, config):
    url = config["ollama_url"]

    if not url.startswith(("http://", "https://")):
        err(f"Invalid Ollama URL scheme: {url}. Must start with http:// or https://")

    model = config.get("model", "")
    if not model:
        err("No model specified. Set one with: git aicm config model <name>")

    try:
        urllib.request.urlopen(f"{url}/api/tags", timeout=5)
    except Exception:
        err(f"Cannot reach Ollama at {url}. Is it running? Start with: ollama serve")

    req = urllib.request.Request(
        f"{url}/api/generate",
        data=json.dumps({"model": config["model"], "prompt": prompt, "stream": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        message = []
        with urllib.request.urlopen(req, timeout=120) as resp:  # Reduced from 300s
            for line in resp:
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue
                    
                if "response" not in chunk or "done" not in chunk:
                    continue
                text = chunk["response"]
                print(text, end="", flush=True)
                message.append(text)
                if chunk["done"]:
                    break
        print()
        return "".join(message)
    except TimeoutError:
        err("Timed out waiting for Ollama. Try stopping other models: ollama stop <model>")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            err(f"Model '{config['model']}' not found. Pull it with: ollama pull {config['model']}")
        err(f"Ollama error: {e}")
    except (ConnectionError, urllib.error.URLError):
        err("Lost connection to Ollama. Is it still running?")


def setup(config):
    import json
    import subprocess
    import re

    url = input(f"\nOllama URL [{config.get('ollama_url', 'http://localhost:11434')}]: ").strip()
    config["ollama_url"] = url or config.get("ollama_url", "http://localhost:11434")
    url = config["ollama_url"]

    try:
        urllib.request.urlopen(f"{url}/api/tags", timeout=5)
    except Exception:
        err("Ollama is not running. Start it with: ollama serve")

    model = config.get("model", "")
    # Validate model name to prevent command injection
    if not re.match(r'^[a-zA-Z0-9._:-]+$', model):
        err(f"Invalid model name: {model}")
    
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read())
            has_model = any(m["name"].startswith(model) for m in data.get("models", []))
    except Exception:
        has_model = False

    if has_model:
        print(f"\nModel '{model}' is already available.")
    else:
        print(f"\nPulling model '{model}'...")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
        except subprocess.CalledProcessError:
            err(f"Failed to pull model '{model}'. Check the model name and try again.")
    return config
