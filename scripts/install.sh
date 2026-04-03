#!/usr/bin/env bash
# MilkyWay Installation Script
# Installs MilkyWay and checks/installs optional dependencies

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

echo -e "${CYAN}"
cat << 'EOF'
  __  __ _ _ _          __        __
 |  \/  (_) | | ___   __\ \      / /_ _ _   _
 | |\/| | | | |/ / | | \ \ /\ / / _` | | | |
 | |  | | | |   <| |_| |\ V  V / (_| | |_| |
 |_|  |_|_|_|_|\_\\__, | \_/\_/ \__,_|\__, |
                  |___/                |___/

  The Galactic CTF Orchestrator v1.0.0
  by kazim-45 — github.com/kazim-45/milkyway
EOF
echo -e "${RESET}"

# ── Detect OS ─────────────────────────────────────────────────────────────────

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &>/dev/null; then
            echo "debian"
        elif command -v pacman &>/dev/null; then
            echo "arch"
        elif command -v dnf &>/dev/null; then
            echo "fedora"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo -e "${BOLD}Detected OS:${RESET} $OS"

# ── Python check ──────────────────────────────────────────────────────────────

echo -e "\n${BOLD}[1/5] Checking Python...${RESET}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}Python 3 not found. Please install Python 3.9+${RESET}"
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}✓ Python ${PYTHON_VER}${RESET}"

# ── Install MilkyWay ──────────────────────────────────────────────────────────

echo -e "\n${BOLD}[2/5] Installing MilkyWay...${RESET}"
pip3 install milkyway-ctf --quiet
echo -e "${GREEN}✓ MilkyWay installed${RESET}"

# ── Check tools ───────────────────────────────────────────────────────────────

echo -e "\n${BOLD}[3/5] Checking optional tools...${RESET}"

check_tool() {
    local tool=$1
    local install_hint=$2
    if command -v "$tool" &>/dev/null; then
        echo -e "  ${GREEN}✓${RESET} $tool"
    else
        echo -e "  ${YELLOW}✗${RESET} $tool  ${YELLOW}(optional — $install_hint)${RESET}"
    fi
}

# Core tools
check_tool curl "apt install curl"
check_tool openssl "apt install openssl"
check_tool strings "apt install binutils"
check_tool file "pre-installed on most systems"

# Mercury
check_tool ffuf "go install github.com/ffuf/ffuf@latest"
check_tool sqlmap "pip install sqlmap OR apt install sqlmap"
check_tool nuclei "go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"

# Venus
check_tool hashcat "apt install hashcat OR brew install hashcat"
check_tool john "apt install john"

# Earth
check_tool binwalk "pip install binwalk OR apt install binwalk"
check_tool exiftool "apt install exiftool OR brew install exiftool"
check_tool tshark "apt install tshark"
check_tool steghide "apt install steghide"

# Mars
check_tool objdump "apt install binutils"
check_tool strace "apt install strace"
check_tool ltrace "apt install ltrace"
check_tool r2 "https://rada.re/n/"

# Jupiter
check_tool gdb "apt install gdb"
check_tool checksec "apt install checksec OR pip install checksec"
check_tool ROPgadget "pip install ROPgadget"

# ── Shell completions ─────────────────────────────────────────────────────────

echo -e "\n${BOLD}[4/5] Setting up shell completions...${RESET}"

SHELL_NAME=$(basename "$SHELL")
COMPLETION_DIR="$HOME/.milkyway"
mkdir -p "$COMPLETION_DIR"

if [[ "$SHELL_NAME" == "bash" ]]; then
    _MILKYWAY_COMPLETE=bash_source milkyway > "$COMPLETION_DIR/milkyway-complete.bash" 2>/dev/null || true
    BASHRC="$HOME/.bashrc"
    if ! grep -q "milkyway-complete" "$BASHRC" 2>/dev/null; then
        echo "source $COMPLETION_DIR/milkyway-complete.bash" >> "$BASHRC"
        echo -e "${GREEN}✓ Bash completions added to $BASHRC${RESET}"
    fi
elif [[ "$SHELL_NAME" == "zsh" ]]; then
    _MILKYWAY_COMPLETE=zsh_source milkyway > "$COMPLETION_DIR/milkyway-complete.zsh" 2>/dev/null || true
    ZSHRC="$HOME/.zshrc"
    if ! grep -q "milkyway-complete" "$ZSHRC" 2>/dev/null; then
        echo "source $COMPLETION_DIR/milkyway-complete.zsh" >> "$ZSHRC"
        echo -e "${GREEN}✓ Zsh completions added to $ZSHRC${RESET}"
    fi
else
    echo -e "${YELLOW}Manual completion setup needed for $SHELL_NAME${RESET}"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo -e "\n${BOLD}[5/5] Verifying installation...${RESET}"
if command -v milkyway &>/dev/null; then
    echo -e "${GREEN}✓ milkyway command available${RESET}"
    milkyway --version
else
    echo -e "${YELLOW}milkyway not in PATH. Try: export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
fi

echo -e "\n${BOLD}${GREEN}🌌 MilkyWay is ready!${RESET}\n"
echo -e "Quick start:"
echo -e "  ${CYAN}milkyway${RESET}                                    # Launch TUI dashboard"
echo -e "  ${CYAN}milkyway challenge new web1 --category web${RESET}  # Create a challenge"
echo -e "  ${CYAN}milkyway mercury fuzz http://target.com/FUZZ${RESET} # Start fuzzing"
echo -e "  ${CYAN}milkyway saturn log${RESET}                         # View run history"
echo -e "  ${CYAN}milkyway pluto suggest 'base64 string found'${RESET} # Ask Pluto"
echo -e "\nDocs: ${CYAN}https://github.com/kazim-45/milkyway${RESET}"
