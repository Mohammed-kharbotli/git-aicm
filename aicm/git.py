import re
import subprocess
from aicm.utils import err

TICKET_PATTERN = re.compile(r"[A-Z][A-Z0-9]+-\d+")


def get_diff():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
        )
        if result.returncode != 0:
            err("Not a git repository. Run this from inside a git project.")
        
        # Try staged diff first
        diff = subprocess.run(
            ["git", "diff", "--staged"], capture_output=True, text=True
        ).stdout.strip()
        
        # Only try unstaged if staged is empty
        if not diff:
            diff = subprocess.run(
                ["git", "diff"], capture_output=True, text=True
            ).stdout.strip()
        return diff
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        err(f"Git command failed: {e}")


def get_diff_stat():
    try:
        # Try staged diff stat first
        stat = subprocess.run(
            ["git", "diff", "--staged", "--stat"], capture_output=True, text=True
        ).stdout.strip()
        
        # Only try unstaged if staged is empty
        if not stat:
            stat = subprocess.run(
                ["git", "diff", "--stat"], capture_output=True, text=True
            ).stdout.strip()
        return stat
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        err(f"Git command failed: {e}")


def get_ticket():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True
        )
        branch = result.stdout.strip()
        
        # Validate git command output
        if not branch or result.returncode != 0 or len(branch) > 200:
            return None
        
        # Additional validation for branch name format
        if not re.match(r'^[a-zA-Z0-9/_.-]+$', branch):
            return None
            
        # Find all ticket matches and return the first valid one
        matches = TICKET_PATTERN.findall(branch)
        if not matches:
            return None
            
        # Additional validation - ensure ticket format is reasonable (inclusive bounds)
        ticket = matches[0]
        if len(ticket) < 3 or len(ticket) > 20:
            return None
            
        return ticket
    except (subprocess.SubprocessError, FileNotFoundError):
        return None
