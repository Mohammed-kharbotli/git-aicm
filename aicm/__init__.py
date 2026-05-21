import argparse
import sys
from importlib.metadata import version as _pkg_version

from aicm.backends import BACKENDS
from aicm.completions import cmd_completions
from aicm.config import get_config, load_config, load_project_config, save_config, VALID_KEYS, validate_config_value
from aicm.git import get_diff, get_diff_stat, get_ticket, TICKET_PATTERN
from aicm.interactive import interactive_commit, load_message, clear_message
from aicm.prompts import FORMATS, get_prompt
from aicm.setup import cmd_setup
from aicm.utils import err

try:
    __version__ = _pkg_version("git-aicm")
except Exception:
    __version__ = "0.1.0"

MAX_DIFF_LINES = 500

_DOC_EXTENSIONS = {".md", ".rst", ".txt", ".toml", ".cfg", ".ini", ".yaml", ".yml", ".json"}


def _prioritize_code_hunks(lines, limit):
    code_lines = []
    doc_lines = []
    current = code_lines
    for line in lines:
        if line.startswith("diff --git"):
            parts = line.split()
            path = parts[-1] if parts else ""
            current = doc_lines if any(path.endswith(ext) for ext in _DOC_EXTENSIONS) else code_lines
        current.append(line)
    combined = code_lines + doc_lines
    return "\n".join(combined[:limit])


def cmd_config(args):
    project = getattr(args, "project", False)
    config = load_project_config() if project else load_config()
    key = args.key
    value = args.value

    if not key:
        if not config:
            label = "project" if project else "global"
            print(f"No {label} config file. Run 'git aicm config <key> <value>'.")
            return
        for k, v in config.items():
            print(f"{k} = {v}")
        return

    if key not in VALID_KEYS:
        err(f"Invalid config key: {key}. Valid keys: {', '.join(sorted(VALID_KEYS))}")

    if value is None:
        if key in config:
            print(config[key])
        else:
            print(f"{key} is not set")
        return

    error = validate_config_value(key, value)
    if error:
        err(error)

    config[key] = value
    save_config(config, project=project)
    label = "project" if project else "global"
    print(f"{key} = {value} ({label})")


def cmd_generate(args):
    saved = load_message()
    if saved and sys.stdin.isatty():
        print(f"Found saved message:\n\n{saved}\n")
        choice = input("[c]ommit / [e]dit / [d]iscard and regenerate? ").strip().lower()
        if choice in ("c", "e"):
            interactive_commit(saved)
            return
        elif choice == "d":
            clear_message()
        else:
            return

    cli_overrides = {k: v for k, v in vars(args).items() if k not in ("command", "dry_run", "detailed")}
    config = get_config(cli_overrides)
    config["detailed"] = getattr(args, "detailed", False)

    if config["backend"] not in BACKENDS:
        err(f"Unknown backend: {config['backend']}. Use: {', '.join(BACKENDS)}")

    fmt = config.get("format", "conventional")
    if fmt not in FORMATS:
        err(f"Unknown format: {fmt}. Use: {', '.join(FORMATS)}")

    diff = get_diff()
    if not diff:
        err("No changes found (staged or unstaged).")

    stat = None
    lines = diff.splitlines()
    if len(lines) > MAX_DIFF_LINES:
        print(f"Diff is {len(lines)} lines, summarizing with stats + key hunks.", file=sys.stderr)
        stat = get_diff_stat()
        diff = _prioritize_code_hunks(lines, MAX_DIFF_LINES)

    context = config.get("context")
    detailed = config.get("detailed", False)
    message = BACKENDS[config["backend"]](get_prompt(fmt, diff, stat=stat, context=context, detailed=detailed), config)
    if not message:
        err("Backend returned an empty message. Try again or use a different model.")

    ticket = config.get("ticket")
    if ticket and not TICKET_PATTERN.fullmatch(ticket):
        err(f"Invalid ticket format: {ticket}. Expected format: PROJ-123")
    
    # Get ticket from branch if not provided via CLI
    if not ticket:
        ticket = get_ticket()
        # Validate branch-extracted ticket as well
        if ticket and not TICKET_PATTERN.fullmatch(ticket):
            print(f"Warning: Invalid ticket format from branch: {ticket}. Skipping.", file=sys.stderr)
            ticket = None
    
    if ticket:
        message = f"{message.rstrip()}\n\nRefs: {ticket}"
        print(f"\nRefs: {ticket}")

    if getattr(args, "dry_run", False):
        return

    interactive_commit(message)


def main():
    parser = argparse.ArgumentParser(
        prog="git-aicm",
        description="AI-powered git commit message generator",
        epilog="""Examples:
  git aicm                    # Generate commit message (default: ollama)
  git aicm --detailed         # Include bullet points explaining changes
  git aicm --backend bedrock  # Use AWS Bedrock instead
  git aicm --context "deprecation fix"  # Give AI context about the change
  git aicm --dry-run          # Preview message without committing
  git aicm setup              # Interactive configuration
  git aicm config backend     # View current backend
  git aicm config backend ollama  # Set backend to ollama""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", action="version", version=f"git-aicm {__version__}")
    sub = parser.add_subparsers(dest="command", title="Commands", metavar="COMMAND")

    sub.add_parser("setup", help="Interactive setup wizard")

    cfg = sub.add_parser("config", help="View or set config values")
    cfg.add_argument("key", nargs="?", help="Config key to get or set")
    cfg.add_argument("value", nargs="?", help="Value to set")
    cfg.add_argument("--project", "-p", action="store_true", help="Use project config instead of global")

    comp = sub.add_parser("completions", help="Generate shell completions")
    comp.add_argument("shell", choices=["bash", "zsh"], help="Shell type")

    gen = sub.add_parser("generate", help="Generate a commit message (default command)")
    gen.add_argument("--backend", choices=BACKENDS.keys(), help="LLM backend to use")
    gen.add_argument("--model", help="Model name to use")
    gen.add_argument("--ollama-url", dest="ollama_url", help="Ollama server URL")
    gen.add_argument("--profile", help="AWS profile name")
    gen.add_argument("--format", choices=FORMATS, help="Commit message format")
    gen.add_argument("--ticket", help="Ticket reference (e.g. PROJ-123)")
    gen.add_argument("--context", help="Extra context for the AI (e.g. 'deprecation fix')")
    gen.add_argument("--detailed", action="store_true", help="Include bullet points explaining changes")
    gen.add_argument("--dry-run", action="store_true", help="Print message without committing")

    # Root level arguments (for when no subcommand is used)
    parser.add_argument("--backend", choices=BACKENDS.keys(), dest="r_backend", metavar="BACKEND", help="LLM backend to use")
    parser.add_argument("--model", dest="r_model", metavar="MODEL", help="Model name to use")
    parser.add_argument("--ollama-url", dest="r_ollama_url", metavar="URL", help="Ollama server URL")
    parser.add_argument("--profile", dest="r_profile", metavar="PROFILE", help="AWS profile name")
    parser.add_argument("--format", choices=FORMATS, dest="r_format", metavar="FORMAT", help="Commit message format")
    parser.add_argument("--ticket", dest="r_ticket", metavar="TICKET", help="Ticket reference (e.g. PROJ-123)")
    parser.add_argument("--context", dest="r_context", metavar="CONTEXT", help="Extra context for the AI (e.g. 'deprecation fix')")
    parser.add_argument("--detailed", action="store_true", dest="r_detailed", help="Include bullet points explaining changes")
    parser.add_argument("--dry-run", action="store_true", dest="r_dry_run", help="Print message without committing")

    args = parser.parse_args()

    try:
        if args.command == "setup":
            cmd_setup(args)
        elif args.command == "config":
            cmd_config(args)
        elif args.command == "completions":
            cmd_completions(args)
        elif args.command == "generate":
            cmd_generate(args)
        else:
            args.backend = args.r_backend
            args.model = args.r_model
            args.ollama_url = args.r_ollama_url
            args.profile = args.r_profile
            args.format = args.r_format
            args.ticket = args.r_ticket
            args.context = args.r_context
            args.detailed = args.r_detailed
            args.dry_run = args.r_dry_run
            args.command = None
            cmd_generate(args)
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        sys.exit(130)

    try:
        from aicm.update import check_for_update
        latest = check_for_update(__version__)
        if latest:
            print(f"\nUpdate available: {__version__} → {latest}. Run: curl -fsSL https://raw.githubusercontent.com/Mohammed-kharbotli/git-aicm/main/install.sh | bash", file=sys.stderr)
    except Exception:
        pass
