import re
import subprocess
from aicm.utils import err

TICKET_PATTERN = re.compile(r"[A-Z][A-Z0-9]+-\d+")


def get_git_dir():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _staged_or_unstaged(*extra_args):
    try:
        proc = subprocess.run(
            ["git", "diff", "--staged", *extra_args], capture_output=True, text=True
        )
        if proc.returncode != 0:
            err(f"Git command failed: {proc.stderr.strip()}")
        result = proc.stdout.strip()
        if not result:
            proc = subprocess.run(
                ["git", "diff", *extra_args], capture_output=True, text=True
            )
            if proc.returncode != 0:
                err(f"Git command failed: {proc.stderr.strip()}")
            result = proc.stdout.strip()
        return result
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        err(f"Git command failed: {e}")


def get_diff():
    if not get_git_dir():
        err("Not a git repository. Run this from inside a git project.")
    diff = _staged_or_unstaged()
    if diff and len(diff) > 1_000_000:
        err("Diff is too large (>1MB). Break your changes into smaller commits.")
    return diff


def get_diff_stat():
    stat = _staged_or_unstaged("--stat")
    if stat and len(stat) > 100_000:
        err("Diff stat is too large (>100KB). Break your changes into smaller commits.")
    return stat


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
