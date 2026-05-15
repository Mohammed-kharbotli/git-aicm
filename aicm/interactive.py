import os
import re
import subprocess
import sys
import tempfile

from aicm.git import get_git_dir


def _msg_path():
    git_dir = get_git_dir()
    if not git_dir:
        return None
    return os.path.join(git_dir, "AICM_MSG")


def save_message(message):
    path = _msg_path()
    if path:
        with open(path, "w") as f:
            f.write(message)
    return path


def load_message():
    path = _msg_path()
    if path and os.path.exists(path):
        with open(path) as f:
            return f.read().strip()
    return None


def clear_message():
    path = _msg_path()
    if path and os.path.exists(path):
        os.unlink(path)


def _validate_commit_message(message):
    if not message or not message.strip():
        return False, "Empty commit message"

    dangerous_patterns = [
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',
        r'\$\{[^}]*\}',
        r'\$\([^)]*\)',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, message):
            return False, "Commit message contains potentially unsafe characters or patterns"

    if len(message) > 2000:
        return False, "Commit message is extremely long - please edit to be more concise"

    return True, None


def _try_commit(message, skip_hooks=False):
    cmd = ["git", "commit", "-m", message]
    if skip_hooks:
        cmd.append("--no-verify")
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("Commit failed (hook or git error). Message preserved.", file=sys.stderr)
        return False


def interactive_commit(message):
    if not sys.stdin.isatty():
        print("Not a terminal, skipping interactive commit.", file=sys.stderr)
        return

    is_valid, error = _validate_commit_message(message)
    if not is_valid:
        print(f"Invalid commit message: {error}", file=sys.stderr)
        return

    hook_failed = False

    while True:
        if hook_failed:
            choice = input("\n[c]ommit / [e]dit / [s]kip hooks / [f]ix & retry later / [r]eject? ").strip().lower()
        else:
            choice = input("\n[c]ommit / [e]dit / [r]eject? ").strip().lower()
        if choice in ("c", "s"):
            if _try_commit(message, skip_hooks=(choice == "s" and hook_failed)):
                clear_message()
                return
            hook_failed = True
            continue
        elif choice == "f" and hook_failed:
            path = save_message(message)
            print("Message saved. Fix your code, then run: git aicm")
            return
        elif choice == "e":
            edited_message = edit_message(message)
            if edited_message:
                is_valid, error = _validate_commit_message(edited_message)
                if is_valid:
                    message = edited_message
                    if _try_commit(message):
                        clear_message()
                        return
                    hook_failed = True
                    continue
                else:
                    print(f"Invalid commit message: {error}", file=sys.stderr)
                    continue
            else:
                print("Empty message, commit aborted.")
                return
        elif choice == "r":
            print("Commit aborted.")
            return


def edit_message(message):
    editor = os.environ.get("EDITOR", "vi")
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
            f.write(message)
            path = f.name

        try:
            subprocess.run([editor, path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Editor failed: {e}", file=sys.stderr)
            return message
        except FileNotFoundError:
            print(f"Editor '{editor}' not found. Set EDITOR environment variable.", file=sys.stderr)
            return message

        with open(path) as edited:
            edited_message = edited.read().strip()
            return edited_message if edited_message else None
    finally:
        if path and os.path.exists(path):
            os.unlink(path)
