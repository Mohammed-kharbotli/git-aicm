#!/usr/bin/env bash
set -e

# git-aicm installer script
# Usage: curl -fsSL https://raw.githubusercontent.com/Mohammed-kharbotli/git-aicm/main/install.sh | bash

REPO_URL="https://github.com/Mohammed-kharbotli/git-aicm"
INSTALL_DIR="$HOME/.local/share/git-aicm"
BIN_DIR="$HOME/.local/bin"
TEMP_DIR=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1" >&2
    exit 1
}

cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup EXIT

check_dependencies() {
    info "Checking dependencies..."
    
    # Check Python 3.9+
    if ! command -v python3 >/dev/null 2>&1; then
        error "Python 3 is required but not installed. Install with:
  macOS: brew install python
  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv
  Windows: Download from python.org"
    fi
    
    # Check Python version
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
        error "Python 3.9+ is required. Found: $python_version"
    fi
    
    # Check git
    if ! command -v git >/dev/null 2>&1; then
        error "Git is required but not installed."
    fi
    
    success "Dependencies check passed"
}

detect_install_method() {
    if command -v git >/dev/null 2>&1 && [[ -n "${GITHUB_REPOSITORY:-}" ]]; then
        echo "git"
    elif command -v curl >/dev/null 2>&1; then
        echo "curl"
    elif command -v wget >/dev/null 2>&1; then
        echo "wget"
    else
        error "Neither curl nor wget is available for downloading"
    fi
}

download_with_git() {
    info "Cloning repository..."
    git clone "$REPO_URL" "$TEMP_DIR"
}

extract_archive() {
    if command -v unzip >/dev/null 2>&1; then
        unzip -q "$TEMP_DIR/repo.zip" -d "$TEMP_DIR"
        mv "$TEMP_DIR"/git-aicm-main/* "$TEMP_DIR/"
        rmdir "$TEMP_DIR/git-aicm-main"
        rm -f "$TEMP_DIR/repo.zip"
    else
        error "unzip is required to extract the downloaded archive"
    fi
}

download_with_curl() {
    info "Downloading with curl..."
    mkdir -p "$TEMP_DIR"
    curl -fsSL "$REPO_URL/archive/refs/heads/main.zip" -o "$TEMP_DIR/repo.zip"
    extract_archive
}

download_with_wget() {
    info "Downloading with wget..."
    mkdir -p "$TEMP_DIR"
    wget -q "$REPO_URL/archive/refs/heads/main.zip" -O "$TEMP_DIR/repo.zip"
    extract_archive
}

install_git_aicm() {
    local method="$1"
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    
    # Download source
    case "$method" in
        git)
            download_with_git
            ;;
        curl)
            download_with_curl
            ;;
        wget)
            download_with_wget
            ;;
        *)
            error "Unknown download method: $method"
            ;;
    esac
    
    # Verify we have the files we need
    if [[ ! -f "$TEMP_DIR/git-aicm" || ! -f "$TEMP_DIR/pyproject.toml" ]]; then
        error "Downloaded files are incomplete. Missing git-aicm script or pyproject.toml"
    fi
    
    info "Installing git-aicm to $INSTALL_DIR..."
    
    # Remove existing installation
    if [[ -d "$INSTALL_DIR" ]]; then
        warn "Removing existing installation at $INSTALL_DIR"
        rm -rf "$INSTALL_DIR"
    fi
    
    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    
    # Copy only necessary files
    cp -r "$TEMP_DIR"/aicm "$INSTALL_DIR/"
    cp "$TEMP_DIR"/{git-aicm,pyproject.toml,LICENSE} "$INSTALL_DIR/"
    
    # Make git-aicm executable and create symlink
    chmod +x "$INSTALL_DIR/git-aicm"
    
    # Remove existing symlink if it exists
    if [[ -L "$BIN_DIR/git-aicm" ]]; then
        rm "$BIN_DIR/git-aicm"
    fi
    
    ln -s "$INSTALL_DIR/git-aicm" "$BIN_DIR/git-aicm"
    
    success "git-aicm installed successfully"
}

setup_path() {
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        warn "~/.local/bin is not in your PATH"
        
        # Detect shell and add to appropriate RC file
        local shell_rc=""
        if [[ -n "${ZSH_VERSION:-}" || "$SHELL" == *"zsh"* ]]; then
            shell_rc="$HOME/.zshrc"
        elif [[ -n "${BASH_VERSION:-}" || "$SHELL" == *"bash"* ]]; then
            shell_rc="$HOME/.bashrc"
        fi
        
        if [[ -n "$shell_rc" ]]; then
            echo ""
            echo "To add ~/.local/bin to your PATH, run:"
            echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> $shell_rc"
            echo "  source $shell_rc"
        else
            echo ""
            echo "Add ~/.local/bin to your PATH by adding this line to your shell's RC file:"
            echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
    fi
}

verify_installation() {
    info "Verifying installation..."
    
    if [[ -x "$BIN_DIR/git-aicm" ]]; then
        success "git-aicm is installed and executable"
        
        # Test basic functionality
        if "$BIN_DIR/git-aicm" --version >/dev/null 2>&1; then
            success "git-aicm is working correctly"
        else
            warn "git-aicm is installed but may have issues. Try running: git aicm --version"
        fi
    else
        error "Installation verification failed. git-aicm is not executable at $BIN_DIR/git-aicm"
    fi
}

show_next_steps() {
    echo ""
    echo -e "${GREEN}🎉 Installation complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: git aicm setup"
    echo "  2. Configure your preferred backend and model"
    echo "  3. Start using: git aicm"
    echo ""
    echo "For help: git aicm --help"
    echo "Documentation: $REPO_URL"
}

main() {
    echo -e "${BLUE}git-aicm installer${NC}"
    echo ""
    
    check_dependencies
    
    local method
    method=$(detect_install_method)
    info "Using $method for download"
    
    install_git_aicm "$method"
    setup_path
    verify_installation
    show_next_steps
}

# Allow script to be sourced for testing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi