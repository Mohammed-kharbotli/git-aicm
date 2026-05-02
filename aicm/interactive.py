import os
import re
import subprocess
import sys
import tempfile


def _validate_commit_message(message):
    """Validate commit message for safety and basic format requirements."""
    if not message or not message.strip():
        return False, "Empty commit message"
    
    # Check for dangerous command injection patterns only
    dangerous_patterns = [
        r';\s*[a-zA-Z]',  # Semicolon command separator followed by commands
        r'\|\s*[a-zA-Z]',  # Pipe followed by commands
        r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]',  # Control characters (excluding \t, \n, \r)
        r'\$\{[^}]*\}',  # Variable expansion ${var}
        r'\$\([^)]*\)',  # Command substitution $(cmd)
        r'`[^`]+`',  # Backtick command substitution (only when paired with content)
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
        choice = input("\n[c]ommit / [e]dit / [r]eject? ").strip().lower()
        if choice == "c":
            try:
                subprocess.run(["git", "commit", "-m", message], check=True)
            except subprocess.CalledProcessError:
                print("Git commit failed.", file=sys.stderr)
            return
        elif choice == "e":
            edited_message = edit_message(message)
            if edited_message:
                is_valid, error = _validate_commit_message(edited_message)
                if is_valid:
                    try:
                        subprocess.run(["git", "commit", "-m", edited_message], check=True)
                    except subprocess.CalledProcessError:
                        print("Git commit failed.", file=sys.stderr)
                else:
                    print(f"Invalid commit message: {error}", file=sys.stderr)
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
