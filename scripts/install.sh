#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  MilkyWay CTF Suite — Production Installer v2.0
#  Usage: curl -sSL https://raw.githubusercontent.com/kazim-45/milkyway/main/scripts/install.sh | bash
#  Or:    bash scripts/install.sh [--full]
#
#  --full : also install system tools (nmap, binutils, hashcat, tshark…)
#           requires root / sudo on Linux
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail
FULL_INSTALL=0
[[ "${1:-}" == "--full" ]] && FULL_INSTALL=1

# ── Colors ────────────────────────────────────────────────────────────────────
C="\033[0;36m"; G="\033[0;32m"; Y="\033[0;33m"
R="\033[0;31m"; B="\033[1m"; E="\033[0m"
ok()   { echo -e "${G}[+]${E} $*"; }
info() { echo -e "${C}[*]${E} $*"; }
warn() { echo -e "${Y}[!]${E} $*"; }
err()  { echo -e "${R}[✗]${E} $*"; exit 1; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${C}"
cat << 'BANNER'
  __  __ _ _ _          __        __
 |  \/  (_) | | ___   __\ \      / /_ _ _   _
 | |\/| | | | |/ / | | \ \ /\ / / _` | | | |
 | |  | | | |   <| |_| |\ V  V / (_| | |_| |
 |_|  |_|_|_|_|\_\__, | \_/\_/ \__,_|\__, |
                  |___/               |___/

  MilkyWay v2.0 — The Galactic CTF Orchestrator
  by kazim-45  |  github.com/kazim-45/milkyway
BANNER
echo -e "${E}"

# ── OS detection ──────────────────────────────────────────────────────────────
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]];  then OS="macos"; fi
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v apt-get &>/dev/null; then OS="debian"
    elif command -v pacman  &>/dev/null; then OS="arch"
    elif command -v dnf     &>/dev/null; then OS="fedora"
    else OS="linux"; fi
fi
info "Detected OS: $OS"

# ── Python check ──────────────────────────────────────────────────────────────
info "Checking Python 3.9+..."
if ! command -v python3 &>/dev/null; then
    err "Python 3 not found. Install Python 3.9+ and retry."
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MIN=$(python3 -c "import sys; print(1 if sys.version_info >= (3,9) else 0)")
[[ "$PY_MIN" == "1" ]] || err "Python $PY_VER detected. Need 3.9+."
ok "Python $PY_VER"

# ── Install MilkyWay core (pip) ───────────────────────────────────────────────
info "Installing MilkyWay from PyPI (pip)..."
info "This installs ALL Python security libraries — no external tools needed."
info "Libraries: capstone, pwntools, ROPgadget, pycryptodome, androguard, dnspython, PyJWT…"

# Determine pip install mode (venv or system)
if python3 -c "import venv" &>/dev/null; then
    VENV_DIR="$HOME/.milkyway-env"
    if [[ ! -d "$VENV_DIR" ]]; then
        info "Creating virtual environment at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    PIP="$VENV_DIR/bin/pip"
else
    PIP="pip3"
fi

$PIP install --quiet --upgrade pip
$PIP install --quiet milkyway-ctf
ok "MilkyWay core installed"

# ── Shell integration ─────────────────────────────────────────────────────────
info "Setting up shell integration..."
SHELL_NAME=$(basename "$SHELL")
MILKYWAY_BIN="$VENV_DIR/bin/milkyway"
MW_BIN="$VENV_DIR/bin/mw"

# Add venv bin to PATH
SHELL_RC="$HOME/.bashrc"
[[ "$SHELL_NAME" == "zsh" ]] && SHELL_RC="$HOME/.zshrc"
[[ "$SHELL_NAME" == "fish" ]] && SHELL_RC="$HOME/.config/fish/config.fish"

VENV_LINE="export PATH=\"$VENV_DIR/bin:\$PATH\""
if ! grep -qF "milkyway-env" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# MilkyWay CTF Toolkit" >> "$SHELL_RC"
    echo "$VENV_LINE" >> "$SHELL_RC"
    ok "Added $VENV_DIR/bin to $SHELL_RC"
fi

# Tab completion
if [[ "$SHELL_NAME" == "bash" ]]; then
    COMP_FILE="$HOME/.milkyway_complete.bash"
    _MILKYWAY_COMPLETE=bash_source "$MILKYWAY_BIN" > "$COMP_FILE" 2>/dev/null || true
    if ! grep -qF "milkyway_complete" "$SHELL_RC" 2>/dev/null; then
        echo "source $COMP_FILE 2>/dev/null" >> "$SHELL_RC"
        ok "Bash tab completion installed"
    fi
elif [[ "$SHELL_NAME" == "zsh" ]]; then
    COMP_FILE="$HOME/.milkyway_complete.zsh"
    _MILKYWAY_COMPLETE=zsh_source "$MILKYWAY_BIN" > "$COMP_FILE" 2>/dev/null || true
    if ! grep -qF "milkyway_complete" "$SHELL_RC" 2>/dev/null; then
        echo "source $COMP_FILE 2>/dev/null" >> "$SHELL_RC"
        ok "Zsh tab completion installed"
    fi
fi

# ── Optional system tools (--full) ────────────────────────────────────────────
if [[ $FULL_INSTALL -eq 1 ]]; then
    info "Installing system tools (--full mode, requires sudo)..."

    if [[ "$OS" == "debian" ]]; then
        sudo apt-get update -qq
        sudo apt-get install -y --no-install-recommends \
            nmap whois dnsutils netcat-openbsd \
            binutils file xxd exiftool foremost \
            binwalk steghide tshark \
            sqlmap \
            radare2 ltrace strace gdb \
            checksec hashcat john \
            nmap hydra medusa crunch \
            apktool \
            p7zip-full unzip
        ok "System tools installed (Debian/Ubuntu/Kali)"

    elif [[ "$OS" == "macos" ]]; then
        if ! command -v brew &>/dev/null; then
            warn "Homebrew not found. Install from https://brew.sh then re-run with --full"
        else
            brew install nmap whois hashcat john exiftool \
                         binutils radare2 tshark
            ok "System tools installed (macOS)"
        fi
    else
        warn "Automatic system tool install not supported on $OS. Install manually."
    fi

    # Go tools (ffuf, nuclei)
    if command -v go &>/dev/null; then
        info "Installing Go-based tools..."
        go install github.com/ffuf/ffuf/v2@latest && ok "ffuf installed"
        go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && ok "nuclei installed"
    else
        warn "Go not found — ffuf and nuclei not installed (optional)"
        warn "Install Go from https://go.dev/dl/ then run:"
        warn "  go install github.com/ffuf/ffuf/v2@latest"
    fi
fi

# ── Verify installation ────────────────────────────────────────────────────────
info "Verifying installation..."
export PATH="$VENV_DIR/bin:$PATH"
if milkyway --version &>/dev/null; then
    VER=$(milkyway --version 2>&1 | head -1)
    ok "$VER"
else
    warn "milkyway command not found in PATH yet. Restart your shell or run:"
    warn "  source $SHELL_RC"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
ok "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "  MilkyWay v2.0 installed successfully!"
ok "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  ${B}Restart your shell, then:${E}"
echo ""
echo -e "  ${C}mw${E}                          # Interactive mw> shell"
echo -e "  ${C}mw mercury fuzz http://target.com/FUZZ${E}"
echo -e "  ${C}mw venus identify '<hash>'${E}"
echo -e "  ${C}mw pluto suggest 'I found a base64 string'${E}"
echo -e "  ${C}mw saturn log${E}               # View run history"
echo ""
echo -e "  ${Y}Note:${E} All core features work without external tools."
echo -e "  ${Y}Tip:${E}  Run ${C}bash scripts/install.sh --full${E} to also install"
echo -e "        system tools (nmap, hashcat, binutils, etc.)"
echo ""
echo -e "  Docs: ${C}github.com/kazim-45/milkyway${E}"
