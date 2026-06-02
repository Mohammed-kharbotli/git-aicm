# Changelog

## [Unreleased]

### Added
- GitHub Actions CI (tests + linting on push/PR)
- Release workflow with automatic CHANGELOG generation and SHA256 checksums
- Retry logic for all backends (2 retries, 2s delay) for network resilience
- Ruff linter configuration in pyproject.toml
- Project-level config and validation improvements
- Update check functionality (cached, non-blocking GitHub check)

### Fixed
- Double-prompt when committing a saved message

### Changed
- Remove old virtual environment before installing (cleaner upgrades)

## [0.2.0] - 2026-05-15

### Added
- `--context` flag to provide AI with intent information about changes
- `--detailed` flag for bullet-point commit messages
- Ollama as default backend (local, free, no API keys)
- Smart diff truncation (code files prioritized over docs)
- Message preservation on hook failure with `[f]ix & retry later`
- `[s]kip hooks` option after commit failure
- Shell completions (bash + zsh) with backup creation
- Non-TTY safety (skips interactive commit when piped)
- Input validation and command injection prevention
- SSRF protection for Ollama URL
- Config file permissions (`0o600`)
- Download verification in installer

### Fixed
- Subprocess handling for git commit failures
- Commit message format generation

### Changed
- Default backend from Bedrock to Ollama
- Default model to `qwen2.5-coder:7b`
- Ollama timeout reduced from 300s to 120s
- Consolidated and simplified code logic
- Removed unnecessary docstrings

## [0.1.0] - 2026-05-02

### Added
- Initial release
- CLI interface as native git subcommand (`git aicm`)
- Bedrock, Ollama, and Anthropic backends with streaming output
- Conventional and simple commit message formats
- Ticket auto-detection from branch names
- Interactive commit flow (commit/edit/reject)
- `curl | bash` installer
- Self-bootstrapping bash wrapper with venv management
- `git aicm setup` interactive wizard
- `--dry-run` mode
