import os
from pathlib import Path

from aicm.backends import BACKENDS, SETUPS
from aicm.config import CONFIG_PATH, MODEL_DEFAULTS, save_config
from aicm.prompts import FORMATS


def prompt_choice(label, options, default=None):
    print(f"\n{label}")
    for i, opt in enumerate(options, 1):
        marker = " (default)" if opt == default else ""
        print(f"  {i}) {opt}{marker}")
    while True:
        suffix = f" [{default}]" if default else ""
        try:
            value = input(f"Choose{suffix}: ").strip()
        except EOFError:
            if default:
                return default
            raise
        if not value and default:
            return default
        if value.isdigit() and 1 <= int(value) <= len(options):
            return options[int(value) - 1]
        if value in options:
            return value
        print(f"  Invalid choice. Enter 1-{len(options)} or a name.")


def prompt_input(label, default=None):
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"{label}{suffix}: ").strip()
        except EOFError:
            return default
        result = value or default
        if result and len(result) > 500:
            print("Input too long. Please keep it under 500 characters.")
            continue
        return result


def cmd_setup(args):
    print("git-aicm setup")

    backends = list(BACKENDS.keys())
    backend = prompt_choice("Backend", backends, default="ollama")

    model = prompt_input("\nModel", MODEL_DEFAULTS.get(backend, ""))
    config = {"backend": backend, "model": model}

    fmt = prompt_choice("Commit format", FORMATS, default="conventional")
    config["format"] = fmt

    if backend in SETUPS:
        config = SETUPS[backend](config)

    save_config(config)
    print(f"\nConfig saved to {CONFIG_PATH}")

    install_completions()

    print("\nYou're all set! Run 'git aicm' to generate a commit message.")


def detect_shell():
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    if "bash" in shell:
        return "bash"
    return None


def get_rc_file(shell):
    if shell == "zsh":
        return Path.home() / ".zshrc"
    if shell == "bash":
        return Path.home() / ".bashrc"
    return None


COMPLETION_LINE = 'eval "$(git-aicm completions {shell})"'


def install_completions():
    shell = detect_shell()
    if not shell:
        return
    rc = get_rc_file(shell)
    if not rc:
        return
    line = COMPLETION_LINE.format(shell=shell)
    content = rc.read_text() if rc.exists() else ""
    if line in content:
        return
    try:
        choice = input(f"\nEnable tab completions in {rc.name}? [Y/n] ").strip().lower()
    except EOFError:
        return
    if choice in ("", "y", "yes"):
        backup_path = rc.with_suffix(f"{rc.suffix}.backup.{int(__import__('time').time())}")
        try:
            if rc.exists():
                import shutil
                shutil.copy2(rc, backup_path)
                print(f"Backup created: {backup_path}")

            with open(rc, "a") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(f"\n# git-aicm completions\n{line}\n")
            print(f"Completions added to {rc}. Restart your shell or run: source {rc}")
        except OSError as e:
            import sys
            print(f"Failed to modify {rc}: {e}", file=sys.stderr)
            if backup_path.exists():
                backup_path.unlink()
