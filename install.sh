#!/usr/bin/env bash
set -e

# git-aicm installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Mohammed-kharbotli/git-aicm/main/install.sh | bash

REPO_URL="https://github.com/Mohammed-kharbotli/git-aicm"
INSTALL_DIR="$HOME/.local/share/git-aicm"
BIN_DIR="$HOME/.local/bin"
TEMP_DIR=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()    { echo -e "${BLUE}ℹ${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
error()   { echo -e "${RED}✗${NC} $1" >&2; exit 1; }

cleanup() { [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"; }
trap cleanup EXIT

# --- Preflight checks ---

if ! command -v python3 >/dev/null 2>&1; then
    error "Python 3 is required. Install with: brew install python (macOS) or apt install python3 (Linux)"
fi

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    error "Python 3.9+ is required. Found: $(python3 --version 2>/dev/null || echo unknown)"
fi

command -v git >/dev/null 2>&1 || error "Git is required but not installed."

success "Dependencies OK"

# --- Download ---

TEMP_DIR=$(mktemp -d)

if command -v curl >/dev/null 2>&1; then
    info "Downloading with curl..."
    mkdir -p "$TEMP_DIR"
    curl -fsSL "$REPO_URL/archive/refs/heads/main.zip" -o "$TEMP_DIR/repo.zip"
elif command -v wget >/dev/null 2>&1; then
    info "Downloading with wget..."
    mkdir -p "$TEMP_DIR"
    wget -q "$REPO_URL/archive/refs/heads/main.zip" -O "$TEMP_DIR/repo.zip"
elif command -v git >/dev/null 2>&1; then
    info "Cloning repository..."
    git clone --depth 1 "$REPO_URL" "$TEMP_DIR"
else
    error "Need curl, wget, or git to download"
fi

# Extract if we downloaded a zip
if [[ -f "$TEMP_DIR/repo.zip" ]]; then
    command -v unzip >/dev/null 2>&1 || error "unzip is required to extract the archive"
    unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
    mv "$TEMP_DIR"/git-aicm-main/* "$TEMP_DIR/"
    rm -rf "$TEMP_DIR/git-aicm-main"
    rm -f "$TEMP_DIR/repo.zip"
fi

# --- Verify download ---

for f in git-aicm pyproject.toml LICENSE; do
    [[ -s "$TEMP_DIR/$f" ]] || error "Download incomplete: $f missing or empty"
done
[[ -d "$TEMP_DIR/aicm" && -f "$TEMP_DIR/aicm/__init__.py" ]] || error "Download incomplete: aicm/ package missing"

# Try SHA256 verification from latest release (skip if unavailable)
checksum_url="$REPO_URL/releases/latest/download/SHA256SUMS"
checksum_file="$TEMP_DIR/SHA256SUMS"
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$checksum_url" -o "$checksum_file" 2>/dev/null || true
elif command -v wget >/dev/null 2>&1; then
    wget -q "$checksum_url" -O "$checksum_file" 2>/dev/null || true
fi
if [[ -s "$checksum_file" ]]; then
    info "Verifying SHA256 checksum..."
    if command -v sha256sum >/dev/null 2>&1; then
        (cd "$TEMP_DIR" && sha256sum --check SHA256SUMS --quiet 2>/dev/null) && success "Checksum verified" || warn "Checksum mismatch (file layout may differ from release)"
    elif command -v shasum >/dev/null 2>&1; then
        (cd "$TEMP_DIR" && shasum -a 256 --check SHA256SUMS --quiet 2>/dev/null) && success "Checksum verified" || warn "Checksum mismatch (file layout may differ from release)"
    fi
    rm -f "$checksum_file"
fi

# --- Install ---

info "Installing to $INSTALL_DIR..."

[[ -d "$INSTALL_DIR" ]] && rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR" "$BIN_DIR"

cp -r "$TEMP_DIR"/aicm "$INSTALL_DIR/"
cp "$TEMP_DIR"/{git-aicm,pyproject.toml,LICENSE} "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/git-aicm"

[[ -L "$BIN_DIR/git-aicm" ]] && rm "$BIN_DIR/git-aicm"
ln -s "$INSTALL_DIR/git-aicm" "$BIN_DIR/git-aicm"

# Nuke old venv so it rebuilds cleanly
venv="${AICM_VENV:-$HOME/.venvs/git-aicm}"
[[ -d "$venv" ]] && rm -rf "$venv"

success "Installed"

# --- Post-install ---

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    warn "~/.local/bin is not in your PATH"
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo "  Add to ~/.zshrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
    else
        echo "  Add to ~/.bashrc: export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

if "$BIN_DIR/git-aicm" --version >/dev/null 2>&1; then
    success "git-aicm is working"
else
    warn "Installed but may have issues. Try: git aicm --version"
fi

echo ""
echo -e "${GREEN}Done!${NC} Run 'git aicm setup' to configure."
