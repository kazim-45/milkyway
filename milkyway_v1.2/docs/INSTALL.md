# 📦 Installation Guide

## Quick Install (Recommended)

```bash
pip install milkyway-ctf
milkyway --help
```

## One-Line Setup Script

```bash
curl -sSL https://raw.githubusercontent.com/kazim-45/milkyway/main/scripts/install.sh | bash
```

This installs MilkyWay and checks for optional tool dependencies.

## Docker (Zero Dependencies)

```bash
# Pull and run
docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway

# Or build locally
git clone https://github.com/kazim-45/milkyway
cd milkyway
docker build -t milkyway .
docker run -it --rm -v $(pwd):/workspace milkyway
```

## From Source

```bash
git clone https://github.com/kazim-45/milkyway
cd milkyway
pip install -e .           # Basic install
pip install -e ".[llm]"    # With Ollama/OpenAI support
pip install -e ".[dev]"    # With dev tools
```

---

## Optional Tool Dependencies

MilkyWay wraps external tools. The core functions (Venus crypto, basic Earth forensics) work with no external tools. For full capability, install the following:

### ☿ Mercury (Web Security)

| Tool | Install |
|------|---------|
| ffuf | `go install github.com/ffuf/ffuf@latest` |
| sqlmap | `pip install sqlmap` or `apt install sqlmap` |
| nuclei | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| curl | Pre-installed on most systems |

### ♀ Venus (Cryptography)

| Tool | Install |
|------|---------|
| hashcat | `apt install hashcat` or `brew install hashcat` |
| john | `apt install john` |
| openssl | `apt install openssl` |

### ♁ Earth (Forensics)

| Tool | Install |
|------|---------|
| binwalk | `pip install binwalk` or `apt install binwalk` |
| exiftool | `apt install exiftool` or `brew install exiftool` |
| tshark | `apt install tshark` |
| steghide | `apt install steghide` |
| strings/xxd | `apt install binutils` |

### ♂ Mars (Reverse Engineering)

| Tool | Install |
|------|---------|
| objdump/nm/readelf | `apt install binutils` |
| strace | `apt install strace` |
| ltrace | `apt install ltrace` |
| radare2 | [https://rada.re/n/](https://rada.re/n/) |

### ♃ Jupiter (Binary Exploitation)

| Tool | Install |
|------|---------|
| gdb | `apt install gdb` |
| pwntools | `pip install pwntools` |
| checksec | `apt install checksec` or `pip install checksec` |
| ROPgadget | `pip install ROPgadget` |
| ropper | `pip install ropper` |

### ♇ Pluto (AI Assistant)

For AI-powered suggestions, either:

**Option A: Ollama (Local, Free)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull mistral

# Configure MilkyWay
milkyway config set pluto.backend ollama
milkyway config set pluto.model mistral
```

**Option B: OpenAI API**
```bash
milkyway config set pluto.backend openai
milkyway config set pluto.openai_api_key sk-...
```

---

## Kali Linux (Recommended CTF Environment)

```bash
# Most tools are pre-installed on Kali
pip install milkyway-ctf

# Install Go tools
go install github.com/ffuf/ffuf@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

pip install ROPgadget ropper pwntools
```

## macOS (Homebrew)

```bash
brew install ffuf sqlmap hashcat exiftool binutils
pip install milkyway-ctf sqlmap ROPgadget ropper
```

## Shell Completions

### Bash
```bash
_MILKYWAY_COMPLETE=bash_source milkyway >> ~/.bashrc
source ~/.bashrc
```

### Zsh
```bash
_MILKYWAY_COMPLETE=zsh_source milkyway >> ~/.zshrc
source ~/.zshrc
```

### Fish
```bash
_MILKYWAY_COMPLETE=fish_source milkyway > ~/.config/fish/completions/milkyway.fish
```

---

## Verify Installation

```bash
milkyway --version
milkyway tools              # Check all tool availability
milkyway tools --install    # See install hints for missing tools
```
