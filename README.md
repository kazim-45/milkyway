# 🌌 MilkyWay

### *The Galactic CTF Orchestrator*

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20windows-lightgrey)](https://github.com/kazim-45/milkyway)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## 🚀 What is MilkyWay?

**MilkyWay** is a modular, version-controlled CTF toolkit that transforms how security researchers, CTF competitors, and penetration testers interact with their toolchain. It wraps 50+ security tools into a unified, consistent CLI with automatic run versioning, challenge organization, and an AI-powered assistant.

### The Problem It Solves

Every CTF competitor knows the struggle:
- **Setup fatigue** — Installing tools, memorizing obscure flags, re-doing the same prep every competition
- **Context switching** — Jumping between terminals, losing track of what you tried
- **Messy folders** — Challenges scattered everywhere, no structure, lost notes
- **No reproducibility** — "I swear this command worked 10 minutes ago..."
- **Team chaos** — Multiple members trying the same thing, no coordination

MilkyWay turns this chaos into a **structured, auditable, and collaborative experience**.

---

## ⚡ Quick Start

```bash
# Install
pip install milkyway-ctf

# Create your first challenge workspace
milkyway challenge new pico_web1 --category web --url https://challenge.zip

# Start hacking
cd ~/milkyway-challenges/pico_web1
milkyway mercury fuzz http://target.com/FUZZ
milkyway mercury sql 'http://target.com/page?id=1'

# Not sure what to use? Ask Pluto
milkyway pluto suggest "I found a weird base64 string in the HTTP response"

# Review what you've tried
milkyway saturn log

# Redo a successful command
milkyway saturn redo 42

# Launch the interactive TUI
milkyway tui
```

---

## 🪐 Planetary Tool Map

| Planet | Domain | Key Commands |
|--------|--------|--------------|
| **☿ Mercury** | Web Security | `mercury fuzz`, `mercury sql`, `mercury request`, `mercury headers`, `mercury extract`, `mercury scan` |
| **♀ Venus** | Cryptography | `venus identify`, `venus hash`, `venus crack`, `venus encode`, `venus decode`, `venus xor`, `venus factor` |
| **♁ Earth** | Forensics | `earth info`, `earth carve`, `earth strings`, `earth hexdump`, `earth steg`, `earth pcap` |
| **♂ Mars** | Reverse Engineering | `mars disassemble`, `mars info`, `mars symbols`, `mars trace`, `mars r2` |
| **♃ Jupiter** | Binary Exploitation | `jupiter checksec`, `jupiter rop`, `jupiter template`, `jupiter cyclic` |
| **♆ Neptune** | Cloud & Misc | `neptune jwt`, `neptune cloud`, `neptune url` |
| **♇ Pluto** | AI Assistant | `pluto suggest`, `pluto analyze`, `pluto cheatsheet` |
| **🪐 Saturn** | Version Control | `saturn log`, `saturn diff`, `saturn redo`, `saturn status`, `saturn annotate`, `saturn export` |

---

## 🎯 Feature Highlights

### Saturn — Version Control for Hacking

Every command is automatically recorded:

```bash
$ milkyway saturn log
┌────┬─────────────────────┬─────────┬────────┬───────────────────────────────────┬──────┐
│ ID │ Timestamp           │ Planet  │ Action │ Command                           │ Exit │
├────┼─────────────────────┼─────────┼────────┼───────────────────────────────────┼──────┤
│ 42 │ 2025-04-01 14:23:15 │ mercury │ fuzz   │ milkyway mercury fuzz http://...  │ 0    │
│ 41 │ 2025-04-01 14:20:03 │ venus   │ decode │ milkyway venus decode aGVsbG8=    │ 0    │
│ 40 │ 2025-04-01 14:15:22 │ earth   │ carve  │ milkyway earth carve firmware.bin │ 0    │
└────┴─────────────────────┴─────────┴────────┴───────────────────────────────────┴──────┘

$ milkyway saturn redo 40
[Replaying run #40] earth carve firmware.bin

$ milkyway saturn diff 41 42
# Shows output diff between runs
```

### Challenge Workspaces

```bash
$ milkyway challenge new hackthebox_web --category web --url https://app.hackthebox.com/...
✓ Challenge created!

Name:     hackthebox_web
Category: web
Path:     ~/milkyway-challenges/hackthebox_web

# Auto-generated structure:
~/milkyway-challenges/hackthebox_web/
├── .milkyway/          # Local Saturn DB + config
├── files/              # Downloaded challenge artifacts
├── solutions/
│   └── solve.py        # Starter exploit script
├── outputs/            # Tool outputs
├── notes.md            # Your observations
└── README.md           # Auto-generated with metadata
```

### Pluto — AI-Powered Suggestions

```bash
$ milkyway pluto suggest "I found a suspicious file with no extension, it might be an image"

## ♇ Pluto Suggestion

### Earth — detected keyword: file, image

Try these commands:
\```bash
milkyway earth info ./suspicious_file     # Full file analysis
milkyway earth strings ./suspicious_file  # Extract readable strings
milkyway earth hexdump ./suspicious_file  # Inspect raw bytes
milkyway earth carve ./suspicious_file    # Extract embedded files
\```

If it's an image, also check for steganography:
\```bash
milkyway earth steg ./suspicious_file
\```
```

---

## 📦 Installation

```bash
# PyPI (recommended)
pip install milkyway-ctf

# Docker (zero dependencies — everything pre-installed)
docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway

# From source
git clone https://github.com/kazim-45/milkyway
cd milkyway
pip install -e .
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed setup, shell completions, and per-OS instructions.

---

## 🏗️ Architecture

```
milkyway/
├── milkyway/
│   ├── cli/
│   │   ├── main.py              # Root Click CLI + all commands
│   │   └── planets/
│   │       ├── base.py          # Abstract Planet class
│   │       ├── mercury.py       # Web Security
│   │       ├── venus.py         # Cryptography
│   │       ├── earth.py         # Forensics
│   │       ├── mars.py          # Reverse Engineering
│   │       ├── jupiter.py       # Binary Exploitation
│   │       ├── neptune.py       # Cloud & Misc
│   │       └── pluto.py         # AI Assistant
│   ├── core/
│   │   ├── db.py                # Saturn SQLite engine
│   │   ├── runner.py            # Safe subprocess wrapper
│   │   ├── challenge_manager.py # Challenge workspace management
│   │   └── config.py            # User configuration
│   ├── tui/
│   │   └── app.py               # Textual TUI dashboard
│   └── data/
│       └── wordlists/common.txt # Bundled wordlist
├── tests/                       # pytest test suite (~85%+ coverage)
├── docs/                        # Documentation
├── scripts/install.sh           # One-line install script
└── Dockerfile                   # Full CTF environment
```

**Tech stack**: Python 3.9+ · Click · Rich · Textual · SQLite · Ollama/OpenAI

---

## 📖 Documentation

| Resource | Description |
|----------|-------------|
| [INSTALL.md](docs/INSTALL.md) | Detailed setup for all platforms |
| [SATURN.md](docs/SATURN.md) | Saturn version control deep dive |
| `milkyway <planet> --help` | Inline help for every command |
| `milkyway tools` | Check tool availability |
| `milkyway pluto cheatsheet web` | Quick reference sheets |

---

## 🤝 Contributing

MilkyWay welcomes contributions:
- New tool wrappers for existing planets
- New planet implementations
- Bug fixes and performance improvements
- Documentation and write-ups

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📊 Project Status

| Component | Status | Version |
|-----------|--------|---------|
| Core CLI + Saturn | ✅ Stable | 1.0.0 |
| Mercury (Web) | ✅ Stable | 1.0.0 |
| Venus (Crypto) | ✅ Stable | 1.0.0 |
| Earth (Forensics) | ✅ Stable | 1.0.0 |
| Mars (Rev Eng) | 🔄 Beta | 0.9.0 |
| Jupiter (Binary) | 🔄 Beta | 0.9.0 |
| Neptune (Cloud) | 🔄 Beta | 0.9.0 |
| Pluto (AI) | 🧪 Alpha | 0.5.0 |
| TUI Dashboard | 🔄 Beta | 0.9.0 |

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

## 🌌 Author

**Kazim** — [github.com/kazim-45](https://github.com/kazim-45)

```
$ milkyway --version
MilkyWay 1.0.0 | The Galactic CTF Orchestrator
"Not all who wander are lost — some are just fuzzing."
```
