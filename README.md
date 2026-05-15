# git-aicm

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

Stop writing commit messages. Let AI read your diff and do the boring part — you just hit `c` to commit. 🚀

`git add . && git aicm` — that's it. Your diff goes to an LLM, a commit message streams back in real time, and you choose: commit, edit, or reject.

The default backend is **Ollama** with **llama3.2** — fully local, fully free, no API keys needed.

## Prerequisites

- Python 3.9+
- Git
- [Ollama](https://ollama.com) (default backend — local, free, no API keys)
- macOS or Linux (Windows users: use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install))

**Install Ollama:**
```bash
# macOS (Homebrew)
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download
```

Then pull the default model and start the server:
```bash
ollama pull llama3.2
ollama serve
```

> **Note:** `git aicm setup` will offer to pull the model for you if it's not already available.

**Install Python:**
```bash
# macOS (Homebrew)
brew install python

# Ubuntu/Debian
sudo apt install python3 python3-pip python3-venv

# Windows (WSL)
# Install WSL, then follow the Ubuntu/Debian instructions above
```

## Installation

### Quick Install (Recommended)

Install with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/Mohammed-kharbotli/git-aicm/main/install.sh | bash
```

This will:
- Download and install git-aicm to `~/.local/share/git-aicm`
- Create a symlink in `~/.local/bin/git-aicm`
- Verify the installation
- Show next steps

### Manual Installation

1. Clone this repository:
```bash
git clone https://github.com/Mohammed-kharbotli/git-aicm.git
cd git-aicm
```

2. Make it available as a git subcommand:
```bash
ln -s "$(pwd)/git-aicm" /usr/local/bin/git-aicm
```

3. Run the setup wizard:
```bash
git aicm setup
```

The setup wizard will automatically create a Python virtual environment and install dependencies.

## Alternative Installation

If you prefer to manage the Python environment yourself:

```bash
# Bedrock users
pip install .[bedrock]

# Anthropic API users
pip install .[anthropic]

# Ollama users (no additional dependencies needed)
pip install .
```

Then symlink the installed executable:

```bash
ln -s /path/to/installed/git-aicm /usr/local/bin/git-aicm
```

## Uninstall

To remove git-aicm:

```bash
# Remove installation directory
rm -rf ~/.local/share/git-aicm

# Remove symlink
rm ~/.local/bin/git-aicm

# Remove config (optional)
rm ~/.aicm.toml
```

## Usage

```bash
# stage your changes first
git add .

# generate a commit message (default: Ollama)
git aicm

# provide context so the AI knows *why* you're making the change
git aicm --context "fixing deprecation warnings for v2 migration"

# include bullet points explaining the changes
git aicm --detailed

# use Bedrock instead
git aicm --backend bedrock

# use a specific model
git aicm --backend ollama --model codellama

# dry run (print message without committing)
git aicm --dry-run
```

After generating, you'll be prompted to:
- **c** — commit with the generated message
- **e** — edit the message in your `$EDITOR` before committing
- **r** — reject and abort

If a commit fails (e.g. a pre-commit hook rejects it), the message is preserved and you can retry, edit, skip hooks, fix later, or reject.

Choosing **f** (fix & retry later) saves the message to `.git/AICM_MSG` and exits so you can fix your code. Next time you run `git aicm`, it automatically detects the saved message and offers to commit, edit, or discard it.

## Configuration

Run the interactive setup wizard:

```bash
git aicm setup
```

This will:
1. Ask for your preferred backend and model
2. Pull the Ollama model (if not already available) or verify credentials
3. Save your config to `~/.aicm.toml`

### View or change individual settings:

```bash
# view all settings
git aicm config

# view a single setting
git aicm config backend

# set a single setting
git aicm config backend ollama
git aicm config model codellama
git aicm config format simple
```

### Manual config file

Create `~/.aicm.toml`:

```toml
backend = "ollama"
model = "llama3.2"
ollama_url = "http://localhost:11434"
profile = "my-aws-profile"
format = "conventional"
```

CLI arguments override the config file:

```bash
# uses ollama from config, but overrides the model
git aicm --model codellama
```

## Commit Message Formats

| Format | Description | Example |
|--------|-------------|---------|
| `conventional` (default) | Conventional Commits | `fix(auth): validate token expiry` |
| `simple` | Plain summary | `validate token expiry` |

By default, messages are a **single summary line**. Add `--detailed` for bullet points:

```bash
# summary only (default)
git aicm

# summary + bullet points
git aicm --detailed

# change format
git aicm --format simple
```

## Ticket References

A `Refs: TICKET-123` line is automatically appended to the commit message.

**Priority order:**
1. `--ticket TICKET-123` — explicit flag
2. Auto-detected from branch name (e.g. `feature/PROJ-42-login` → `Refs: PROJ-42`)
3. No match — no `Refs:` line

```bash
# explicit ticket
git aicm --ticket PROJ-42

# auto-detect from branch name
git aicm
```

The pattern matches any `UPPERCASE-NUMBER` format (e.g. `JIRA-123`, `PROJ-42`, `ABC-1`).

## Backends

| Backend | Requires | Set via |
|---------|----------|---------|
| `ollama` (default) | [Ollama](https://ollama.com) running locally | `--backend ollama` |
| `bedrock` | AWS credentials (see below) | `--backend bedrock` |
| `anthropic` | Anthropic API key | `--backend anthropic` |

## AWS Credentials (Bedrock)

To use the Bedrock backend, configure your AWS credentials:

```bash
aws configure
```

You'll be prompted for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g. `us-east-1`)
- Output format (just press Enter)

Alternatively, set environment variables:

```bash
export AWS_ACCESS_KEY_ID=<your-access-key>
export AWS_SECRET_ACCESS_KEY=<your-secret-key>
export AWS_DEFAULT_REGION=us-east-1
```

Or use a named profile:

```bash
git aicm --profile my-aws-profile
```

## Anthropic API

Set your API key:

```bash
export ANTHROPIC_API_KEY=<your-key>
```

Or save it in the config:

```bash
git aicm config anthropic_api_key <your-key>
```

Or use the setup wizard which will prompt for it:

```bash
git aicm setup
```

## Troubleshooting

Reinstall the tool (resets the virtual environment):

```bash
git aicm reinstall
```

## Shell Completions

Tab completions for subcommands, backends, formats, and flags.

The setup wizard offers to install them automatically. To install manually:

```bash
# Zsh (add to ~/.zshrc)
eval "$(git-aicm completions zsh)"

# Bash (add to ~/.bashrc)
eval "$(git-aicm completions bash)"
```

## Context Flag

The AI only sees the diff — it doesn't know *why* you're making a change. Use `--context` to give it a hint:

```bash
git aicm --context "deprecation fix for Rails 8"
git aicm --context "tech debt cleanup from sprint 12"
git aicm --context "performance optimization for large datasets"
```

This helps the AI pick the right commit type (`fix:`, `chore:`, `perf:`, etc.) instead of defaulting to `feat:`.

## How it works

1. Reads `git diff --staged` (falls back to `git diff` if nothing staged)
2. Sends the diff + optional context to the configured LLM backend
3. Streams the generated commit message in real time
4. Appends ticket reference (from `--ticket` or branch name)
5. Lets you commit, edit, or reject the message

## Security Features

- **Input validation**: Prevents command injection in commit messages (variable expansion, command substitution, control chars blocked)
- **Prompt injection mitigation**: User context is escaped and delimited to prevent instruction override
- **Configuration validation**: Only accepts valid configuration keys and values
- **API key validation**: Verifies API keys via non-billable `models.list` call
- **Safe subprocess handling**: Proper error handling and returncode checking for all git commands
- **Length limits**: Enforced at source — diff 1MB, stat 100KB, context 500 chars
- **SSRF protection**: Ollama URL scheme validated to `http://`/`https://` only
- **Config file permissions**: Written with `0o600` to protect API keys
- **TOML escaping**: Backslashes and quotes escaped during config serialization
- **Ticket validation**: Uses strict full-match to reject malformed ticket references
- **Bedrock model validation**: Supports region-prefixed model IDs (e.g. `eu.`, `us.`, `ap.`, `me.`, `af.`)
- **Non-TTY safety**: Prints informative message and skips interactive commit when stdin is not a terminal

## License

MIT
