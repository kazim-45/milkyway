<div align="center">
    
```
================================================================================
                                                                                
        ███╗   ███╗██╗██╗     ██╗  ██╗██╗   ██╗██╗    ██╗ █████╗ ██╗   ██╗     
        ████╗ ████║██║██║     ██║ ██╔╝╚██╗ ██╔╝██║    ██║██╔══██╗╚██╗ ██╔╝     
        ██╔████╔██║██║██║     █████╔╝  ╚████╔╝ ██║ █╗ ██║███████║ ╚████╔╝      
        ██║╚██╔╝██║██║██║     ██╔═██╗   ╚██╔╝  ██║███╗██║██╔══██║  ╚██╔╝       
        ██║ ╚═╝ ██║██║███████╗██║  ██╗   ██║   ╚███╔███╔╝██║  ██║   ██║        
        ╚═╝     ╚═╝╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝    ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝        
                                                                                
                   The Galactic CTF Orchestrator                              
               Modular · Versioned · AI-Powered · Planetary                   
                                                                                
================================================================================
```

# MilkyWay CTF Suite

**The Galactic CTF Orchestrator**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Version](https://img.shields.io/badge/version-2.1.0-green?logo=github)](https://github.com/kazim-45/milkyway/releases)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-milkyway--ctf-orange?logo=pypi&logoColor=white)](https://pypi.org/project/milkyway-ctf)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Kali-lightgrey)](https://github.com/kazim-45/milkyway)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

*11 planets · 60 commands · pure-Python core · zero "tool not found" errors*

</div>

---

## 📸 Screenshots

Below are the current MilkyWay interface snapshots from the `assets/` directory.

![MilkyWay dashboard screenshot](assets/mw.png)

![MilkyWay command flow screenshot](assets/mw1.png)

![MilkyWay challenge workspace screenshot](assets/mw2.png)



## What is MilkyWay?

MilkyWay is a **modular, version-controlled CTF toolkit** that unifies every security domain under a single interactive shell. Stop juggling terminals, losing track of what you tried, and fighting tool installs mid-competition. MilkyWay gives you one prompt — `mw>` — that takes you from zero to flag.

### The Problem It Solves

Every CTF competitor knows this pain:
- Spending the first hour installing Kali, tools, and wordlists instead of hacking
- Running the same fuzzer five times because you forgot the output
- Closing a terminal and losing your entire train of thought
- Teammates duplicating each other's work

### The MilkyWay Solution

```
mw> 1              ← Enter Mercury (Web Security)

  ┌─ ☿ MERCURY — Web Security ─────────────────────────────┐
  │  1. mercury fuzz <url>      Directory/file fuzzing      │
  │  2. mercury sql <url>       SQL injection scan          │
  │  3. mercury request <url>   Craft HTTP request          │
  │  ...                                                    │
  └────────────────────────────────────────────────────────┘

[mercury] mw> 1
  ? Target URL: http://target.com/FUZZ
  ? Extensions (Enter to skip): .php,.html

  $ mw mercury fuzz http://target.com/FUZZ --extensions .php,.html
  ▶ Task: mercury fuzz http://target.com/FUZZ…
  ✓ Executing mercury ✓
  FOUND [200] /admin.php  [12345b]
  FOUND [301] /backup/    [0b]
  ✓ Completed | saturn recorded run #42
```

Everything is recorded. Every run is replayable. Every result is searchable.

---

## Feature Highlights

| Feature | Description |
|---------|-------------|
| **11 Planets** | Every major CTF domain in one toolkit |
| **60 Commands** | Fully numbered, navigable from a single shell |
| **Planet Sub-Shell** | Enter a planet once, run numbered commands — no retyping |
| **Guided Args** | Type `1` in a planet → args prompted interactively |
| **Saturn VCS** | Every command auto-recorded, diffable, replayable |
| **Pure-Python Core** | 100% fallback implementations — zero "tool not found" |
| **Challenge Workspaces** | Scaffolded folder per challenge with notes, solve.py, outputs |
| **AI Assistant (Pluto)** | Keyword engine + Ollama/OpenAI for tool suggestions |
| **Tab Completion** | 146 completions across all 11 planets |
| **Colored UI** | Per-planet color coding with live status indicators |
| **Session Export** | One command exports a session to a write-up-ready markdown |

---

## The 11 Planets

<table>
<tr>
  <th>#</th><th>Symbol</th><th>Planet</th><th>Domain</th><th>Commands</th>
</tr>
<tr>
  <td>1</td><td>☿</td><td><b>Mercury</b></td><td>Web Security</td>
  <td><code>fuzz</code> <code>sql</code> <code>request</code> <code>headers</code> <code>extract</code> <code>scan</code></td>
</tr>
<tr>
  <td>2</td><td>♀</td><td><b>Venus</b></td><td>Cryptography</td>
  <td><code>identify</code> <code>hash</code> <code>crack</code> <code>encode</code> <code>decode</code> <code>xor</code> <code>factor</code> <code>rsa</code></td>
</tr>
<tr>
  <td>3</td><td>♁</td><td><b>Earth</b></td><td>Forensics</td>
  <td><code>info</code> <code>carve</code> <code>strings</code> <code>hexdump</code> <code>steg</code> <code>pcap</code></td>
</tr>
<tr>
  <td>4</td><td>♂</td><td><b>Mars</b></td><td>Reverse Engineering</td>
  <td><code>disassemble</code> <code>info</code> <code>symbols</code> <code>trace</code> <code>r2</code></td>
</tr>
<tr>
  <td>5</td><td>♃</td><td><b>Jupiter</b></td><td>Binary Exploitation</td>
  <td><code>checksec</code> <code>rop</code> <code>template</code> <code>cyclic</code></td>
</tr>
<tr>
  <td>6</td><td>♆</td><td><b>Neptune</b></td><td>Cloud & Misc</td>
  <td><code>jwt</code> <code>cloud</code> <code>url</code></td>
</tr>
<tr>
  <td>7</td><td>♅</td><td><b>Uranus</b></td><td>Mobile / IoT</td>
  <td><code>decompile</code> <code>info</code> <code>permissions</code> <code>instrument</code> <code>adb</code> <code>strings</code> <code>ssl-bypass</code></td>
</tr>
<tr>
  <td>8</td><td>🌋</td><td><b>Vulcan</b></td><td>Network Recon & OSINT</td>
  <td><code>portscan</code> <code>quickscan</code> <code>whois</code> <code>dns</code> <code>subdomain</code> <code>banner</code></td>
</tr>
<tr>
  <td>9</td><td>🪐</td><td><b>Titan</b></td><td>Password Attacks</td>
  <td><code>brute</code> <code>spray</code> <code>wordlist</code> <code>cewl</code> <code>analyze</code> <code>mutate</code></td>
</tr>
<tr>
  <td>10</td><td>♇</td><td><b>Pluto</b></td><td>AI Assistant</td>
  <td><code>suggest</code> <code>analyze</code> <code>cheatsheet</code></td>
</tr>
<tr>
  <td>11</td><td>⟳</td><td><b>Saturn</b></td><td>Version Control</td>
  <td><code>log</code> <code>diff</code> <code>redo</code> <code>status</code> <code>annotate</code> <code>export</code></td>
</tr>
</table>

---

## Installation

### Option 1 — pip (Recommended)

```bash
pip install milkyway-ctf
mw
```

This installs MilkyWay **and all Python security libraries** in one command:
`capstone`, `pwntools`, `ROPgadget`, `pycryptodome`, `androguard`, `dnspython`,
`PyJWT`, `paramiko`, `beautifulsoup4`, `sympy`, `pillow`, `passlib`, and more.

**No separate `apt install` or `brew install` required for core functionality.**

### Option 2 — One-Line Script

```bash
curl -sSL https://raw.githubusercontent.com/kazim-45/milkyway/main/scripts/install.sh | bash
```

Optionally with system tools (nmap, hashcat, binutils…):

```bash
bash scripts/install.sh --full
```

### Option 3 — apt (Ubuntu / Kali)

```bash
sudo add-apt-repository ppa:kazim-45/milkyway
sudo apt update
sudo apt install milkyway-ctf
mw
```

### Option 4 — Docker (zero dependencies)

```bash
docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway
```

Everything pre-installed: all Python libraries, nmap, hashcat, ffuf, nuclei, binutils, tshark, and more.

### Option 5 — From Source

```bash
git clone https://github.com/kazim-45/milkyway
cd milkyway
pip install -e ".[dev]"
mw
```

---

## Quick Start

```bash
# Launch interactive shell
mw

# Enter Mercury (Web Security) — stays until you type b
mw> 1
[mercury] mw> 1       ← fuzz (asks for URL interactively)
[mercury] mw> 2       ← sql
[mercury] mw> b       ← back to main menu

# Or type commands directly anywhere
mw> venus decode 'aGVsbG8=' --enc base64
mw> earth strings ./suspicious_file --grep flag
mw> jupiter cyclic 200
mw> pluto suggest "I found a base64 string in the HTTP response"

# Review everything you tried
mw> saturn log
mw> saturn redo 42
mw> saturn diff 12 13

# Organize your work
mw> challenge new pico_web1 --category web --url https://play.picoctf.org/...
cd ~/milkyway-challenges/pico_web1
mw> challenge note pico_web1 "Found SQL injection at /login"
```

---

## Shell Navigation

The MilkyWay shell is modelled after SET and Metasploit with one key improvement: **you stay inside a planet** until you explicitly go back.

```
Main menu           Planet sub-shell
──────────          ────────────────
mw> 1          →    [mercury] mw> 1     ← runs fuzz (prompts URL)
               →    [mercury] mw> 2     ← runs sql
               →    [mercury] mw> fuzz http://site.com/FUZZ  ← direct
               →    [mercury] mw> b     ← back to main menu
mw> 2          →    [venus] mw> 1       ← runs identify
               →    [venus] mw> 5       ← runs decode
               →    [venus] mw> 0       ← back to main menu
```

**Inside any planet:**
- `1`–`N` — run that numbered command (interactive argument prompts)
- `b` / `back` / `0` — return to main menu
- `h` / `help` — re-show this planet's commands
- `cmd [args]` — type any command directly without the planet prefix
- `planet cmd [args]` — fully qualified command also works

---

## Saturn — Version Control for Hacking

Every command you run is automatically versioned.

```bash
# See full history
mw> saturn log
mw> saturn log --planet mercury --limit 50

# Compare two scan results
mw> saturn diff 12 13

# Replay a command that worked
mw> saturn redo 42

# Annotate a run
mw> saturn annotate 42 "This found the admin panel — start here"

# Export your session as a write-up
mw> saturn export abc12345 --output writeup.md
```

The SQLite database lives at `~/.milkyway/global.db` (global) and `.milkyway/local.db` (per challenge). WAL mode, concurrent-safe.

---

## Challenge Workspaces

```bash
mw> challenge new hackthebox_pwn1 --category pwn --url https://app.hackthebox.com/...

# Auto-generated structure:
~/milkyway-challenges/hackthebox_pwn1/
├── .milkyway/          ← Local Saturn DB + config
├── files/              ← Challenge downloads
├── solutions/
│   └── solve.py        ← Pre-filled pwntools template
├── outputs/            ← Tool outputs (linked from Saturn)
├── notes.md            ← Your observations
└── README.md           ← Auto-generated with metadata

# Add notes as you work
mw> challenge note hackthebox_pwn1 "Binary has no canary — ret2win possible"

# Navigate to it
cd $(mw challenge cd hackthebox_pwn1)
```

---

## Pure-Python Fallbacks

MilkyWay runs **every command** even if external tools aren't installed.

| External Tool | MilkyWay Fallback |
|---------------|-------------------|
| `ffuf` | Concurrent `urllib` fuzzer — 2000 paths, 20 threads |
| `sqlmap` | Error-based + boolean SQLi prober — 6 payload families |
| `curl` | Full HTTP client via `urllib.request` |
| `hashcat` / `john` | Python dictionary cracker (MD5/SHA1/SHA256/SHA512) |
| `binwalk` | Signature scanner — carves PNG/JPEG/ZIP/PDF/ELF |
| `xxd` | 16-byte hex formatter |
| `strings` | `re`-based byte pattern extractor |
| `steghide` | JPEG/PNG appended-data scanner |
| `tshark` | Struct-based `.pcap` packet reader |
| `objdump` | **capstone** multi-arch disassembler (pip-installed) |
| `checksec` | ELF header parser — NX/PIE/RELRO/Canary/Fortify |
| `ROPgadget` | capstone ret-backtrack gadget finder |
| `nmap` | Pure `socket` concurrent port scanner |
| `whois` | Direct WHOIS socket query |

---

## Pluto — AI Assistant

```bash
# Keyword-based (always works)
mw> pluto suggest "I found a file with no extension, might be an image"
# → earth info, earth carve, earth steg

# With Ollama (local, free)
ollama pull mistral
mw> config set pluto.backend ollama
mw> pluto suggest "RSA challenge with small e"

# With OpenAI
mw> config set pluto.backend openai
mw> config set pluto.openai_api_key sk-...
mw> pluto suggest "JWT token with HS256 and I have the source code"

# Quick cheatsheets
mw> pluto cheatsheet web
mw> pluto cheatsheet crypto
mw> pluto cheatsheet forensics
```

---

## Configuration

```bash
mw> config show                              # View all settings
mw> config set challenges_dir ~/ctf          # Change challenges directory
mw> config set pluto.backend ollama          # AI backend
mw> config set pluto.model mistral           # Ollama model
mw> tools                                    # Check tool availability
mw> tools --install                          # Show install hints for missing tools
```

Config lives at `~/.milkyway/config.yaml`.

---

## Architecture

```
milkyway/
├── milkyway/
│   ├── cli/
│   │   ├── main.py              # Root Click CLI (1,544 lines)
│   │   └── planets/
│   │       ├── mercury.py       # Web Security
│   │       ├── venus.py         # Cryptography
│   │       ├── earth.py         # Forensics
│   │       ├── mars.py          # Reverse Engineering
│   │       ├── jupiter.py       # Binary Exploitation
│   │       ├── neptune.py       # Cloud & Misc
│   │       ├── uranus.py        # Mobile / IoT
│   │       ├── vulcan.py        # Network Recon
│   │       ├── titan.py         # Password Attacks
│   │       └── pluto.py         # AI Assistant
│   ├── core/
│   │   ├── db.py                # Saturn SQLite engine (509 lines)
│   │   ├── runner.py            # Safe subprocess wrapper
│   │   ├── challenge_manager.py # Workspace scaffolding
│   │   └── config.py            # YAML config
│   ├── shell.py                 # Interactive shell v2.1
│   └── tui/app.py               # Textual TUI dashboard
├── tests/                       # pytest suite
├── debian/                      # Debian packaging
├── .github/workflows/           # CI/CD (test + publish)
├── scripts/
│   ├── install.sh
│   ├── publish_pypi.sh
│   └── setup_apt_repo.sh
└── Dockerfile                   # Full Kali-based image
```

**Tech stack:** Python 3.9+ · Click · Rich · Textual · SQLite (WAL) · capstone · pwntools

---

## Development

```bash
# Fork + clone
git clone https://github.com/kazim-45/milkyway
cd milkyway
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Feature branch workflow
git checkout -b feat/your-feature
# ... make changes ...
pytest tests/ -v
git commit -m "feat(planet): describe your change"
git push origin feat/your-feature
# Open PR on GitHub

# Release
git tag v2.1.0
git push origin v2.1.0   # GitHub Actions → auto-publishes to PyPI
```

See [`docs/GIT_AND_RELEASE_GUIDE.md`](docs/GIT_AND_RELEASE_GUIDE.md) for the full workflow.

---

## Roadmap

See [`ROADMAP.md`](ROADMAP.md) for the full versioned roadmap.

**Next milestone — v2.2 (EuropaUpdate):** write-up generator, Pluto local LLM, Uranus `jadx` integration, 85%+ test coverage.

---

## Contributing

MilkyWay is open-source and welcomes contributions of all kinds.

- **New planet commands** — add a command to any existing planet
- **New planets** — propose a new security domain
- **Bug fixes** — open an issue + PR
- **Tests** — we're aiming for 85%+ coverage
- **Documentation** — write-ups, tutorials, cheatsheets
- **Translations** — help localize the CLI messages

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
Join the community: **[Discord](https://discord.gg/milkyway)** · **[GitHub Discussions](https://github.com/kazim-45/milkyway/discussions)** · **[@milkyway_ctf](https://twitter.com/milkyway_ctf)**

---

## Changelog

| Version | Codename | Highlights |
|---------|----------|-----------|
| **2.1.0** | NebulaDawn | Planet sub-shell with numbered commands, guided arg prompts, sticky planet context |
| **2.0.0** | NebulaDawn | Pure-Python fallbacks for all 60 commands, production Dockerfile, pip bundles all deps |
| **1.2.0** | — | Uranus/Vulcan/Titan planets, Dexter-style colored UI, apt packaging |
| **1.1.0** | — | `mw` shorthand, SET-style shell, tab completion, session system |
| **1.0.0** | — | Core CLI, Saturn VCS, Mercury/Venus/Earth/Mars/Jupiter/Neptune/Pluto/Saturn |

Full changelog: [CHANGELOG.md](CHANGELOG.md)

---

## License

MIT — see [LICENSE](LICENSE).
External tools retain their own licenses.

---

<div align="center">

**Built by [Kazim](https://github.com/kazim-45) · [github.com/kazim-45/milkyway](https://github.com/kazim-45/milkyway)**

*"Not all who wander are lost — some are just fuzzing."*

⭐ Star us on GitHub — every star helps build the definitive CTF toolkit.

</div>
