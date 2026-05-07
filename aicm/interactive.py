import os
import re
import subprocess
import sys
import tempfile


def _validate_commit_message(message):
    """Validate commit message for safety and basic format requirements."""
    if not message or not message.strip():
        return False, "Empty commit message"
    
    # Only block actual shell injection — not normal prose
    dangerous_patterns = [
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters (excluding \t, \n, \r)
        r'\$\{[^}]*\}',  # Variable expansion ${var}
        r'\$\([^)]*\)',  # Command substitution $(cmd)
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, message):
            return False, "Commit message contains potentially unsafe characters or patterns"
    
    # Soft warning for very long messages (AI should prevent this, but just in case)
    if len(message) > 2000:
        return False, "Commit message is extremely long - please edit to be more concise"
    
    return True, None


def interactive_commit(message):
    if not sys.stdin.isatty():
        return
    
    # Validate initial message
    is_valid, error = _validate_commit_message(message)
    if not is_valid:
        print(f"Invalid commit message: {error}", file=sys.stderr)
        return
    
    while True:
        choice = input("\n[c]ommit / [e]dit / [s]kip hooks / [r]eject? ").strip().lower()
        if choice in ("c", "s"):
            cmd = ["git", "commit", "-m", message]
            if choice == "s":
                cmd.append("--no-verify")
            try:
                subprocess.run(cmd, check=True)
                return
            except subprocess.CalledProcessError:
                print("Commit failed (hook or git error). Message preserved.", file=sys.stderr)
                continue
        elif choice == "e":
            edited_message = edit_message(message)
            if edited_message:
                is_valid, error = _validate_commit_message(edited_message)
                if is_valid:
                    message = edited_message
                    try:
                        cmd = ["git", "commit", "-m", message]
                        subprocess.run(cmd, check=True)
                        return
                    except subprocess.CalledProcessError:
                        print("Commit failed (hook or git error). Message preserved.", file=sys.stderr)
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
            return message  # Return original message if editor fails
        except FileNotFoundError:
            print(f"Editor '{editor}' not found. Set EDITOR environment variable.", file=sys.stderr)
            return message
            
        with open(path) as edited:
            edited_message = edited.read().strip()
            return edited_message if edited_message else None
    finally:
        if path and os.path.exists(path):
            os.unlink(path)
