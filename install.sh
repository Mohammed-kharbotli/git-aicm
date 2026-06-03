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

# Resolve latest release tag
LATEST_TAG=""
if command -v curl >/dev/null 2>&1; then
    LATEST_TAG=$(curl -fsSo /dev/null -w '%{redirect_url}' "$REPO_URL/releases/latest" 2>/dev/null | grep -o '[^/]*$' || true)
elif command -v wget >/dev/null 2>&1; then
    LATEST_TAG=$(wget --spider -S "$REPO_URL/releases/latest" 2>&1 | grep -i 'Location:' | grep -o '[^/]*$' | tr -d '\r' || true)
fi

if [[ -n "$LATEST_TAG" ]]; then
    TARBALL_URL="$REPO_URL/releases/download/$LATEST_TAG/git-aicm-$LATEST_TAG.tar.gz"
    info "Downloading $LATEST_TAG..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$TARBALL_URL" -o "$TEMP_DIR/release.tar.gz" 2>/dev/null
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$TARBALL_URL" -O "$TEMP_DIR/release.tar.gz" 2>/dev/null
    fi
fi

# Fall back to main branch if release download failed
if [[ ! -s "$TEMP_DIR/release.tar.gz" ]]; then
    warn "Could not download release, falling back to main branch"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$REPO_URL/archive/refs/heads/main.tar.gz" -o "$TEMP_DIR/release.tar.gz"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$REPO_URL/archive/refs/heads/main.tar.gz" -O "$TEMP_DIR/release.tar.gz"
    elif command -v git >/dev/null 2>&1; then
        info "Cloning repository..."
        git clone --depth 1 "$REPO_URL" "$TEMP_DIR/src"
    else
        error "Need curl, wget, or git to download"
    fi
fi

# Verify and extract tarball
if [[ -s "$TEMP_DIR/release.tar.gz" ]]; then
    # SHA256 verification (only for release downloads)
    if [[ -n "$LATEST_TAG" ]]; then
        checksum_url="$REPO_URL/releases/download/$LATEST_TAG/SHA256SUMS"
        checksum_file="$TEMP_DIR/SHA256SUMS"
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$checksum_url" -o "$checksum_file" 2>/dev/null || true
        elif command -v wget >/dev/null 2>&1; then
            wget -q "$checksum_url" -O "$checksum_file" 2>/dev/null || true
        fi
        if [[ -s "$checksum_file" ]]; then
            info "Verifying SHA256 checksum..."
            # Rename to match the filename in SHA256SUMS
            mv "$TEMP_DIR/release.tar.gz" "$TEMP_DIR/git-aicm-$LATEST_TAG.tar.gz"
            if command -v sha256sum >/dev/null 2>&1; then
                (cd "$TEMP_DIR" && sha256sum --check SHA256SUMS --quiet 2>/dev/null) && success "Checksum verified" || warn "Checksum verification failed"
            elif command -v shasum >/dev/null 2>&1; then
                (cd "$TEMP_DIR" && shasum -a 256 --check SHA256SUMS --quiet 2>/dev/null) && success "Checksum verified" || warn "Checksum verification failed"
            fi
            mv "$TEMP_DIR/git-aicm-$LATEST_TAG.tar.gz" "$TEMP_DIR/release.tar.gz"
            rm -f "$checksum_file"
        fi
    fi
    tar xzf "$TEMP_DIR/release.tar.gz" -C "$TEMP_DIR"
    rm -f "$TEMP_DIR/release.tar.gz"
    # Move files from subdirectory if present (main branch archive)
    subdir=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
    if [[ -n "$subdir" && -f "$subdir/git-aicm" ]]; then
        mv "$subdir"/* "$TEMP_DIR/" 2>/dev/null || true
        mv "$subdir"/.* "$TEMP_DIR/" 2>/dev/null || true
        rm -rf "$subdir"
    fi
elif [[ -d "$TEMP_DIR/src" ]]; then
    mv "$TEMP_DIR"/src/* "$TEMP_DIR/"
    rm -rf "$TEMP_DIR/src"
fi

# --- Verify download ---

for f in git-aicm pyproject.toml LICENSE; do
    [[ -s "$TEMP_DIR/$f" ]] || error "Download incomplete: $f missing or empty"
done
[[ -d "$TEMP_DIR/aicm" && -f "$TEMP_DIR/aicm/__init__.py" ]] || error "Download incomplete: aicm/ package missing"

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
