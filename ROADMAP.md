# MilkyWay CTF Suite — Product Roadmap

> **Status:** Active development · Current: v2.1.0 NebulaDawn
> **Maintained by:** Kazim (kazim-45) · **GitHub:** github.com/kazim-45/milkyway

This roadmap is versioned and realistic. Each milestone has a clear scope, acceptance criteria, and technical notes. Contributions on any milestone are welcome.

---

## Milestone Overview

| Version | Codename | ETA | Theme |
|---------|----------|-----|-------|
| **2.1.0** ✅ | NebulaDawn | Done | Planet sub-shell, numbered commands, guided args |
| **2.2.0** | EuropaUpdate | +3 weeks | Write-up generator, test coverage, Pluto LLM |
| **2.3.0** | GanymedePatch | +6 weeks | Team sync, new planets, CTF platform connectors |
| **2.4.0** | CallistoEdge | +10 weeks | TUI rewrite, plugin system, VS Code extension |
| **3.0.0** | AndromedaCore | +4 months | Web dashboard, distributed Saturn, community plugins |

---

## v2.2.0 — EuropaUpdate (+3 weeks)

**Theme:** Reliability, quality, and write-ups.

### 2.2.1 — Test Coverage to 85%

**Current:** ~40% coverage (core modules tested, planets partially)
**Target:** 85%+

Tasks:
- [ ] Write `tests/test_mercury.py` — mock `urllib.request`, test fuzz/sql/request/extract/scan
- [ ] Write `tests/test_earth.py` — magic byte detection, carving, strings grep, hexdump offsets
- [ ] Write `tests/test_mars.py` — ELF header parsing, security flag detection, capstone disasm
- [ ] Write `tests/test_jupiter.py` — cyclic find, checksec ELF parsing, template generation
- [ ] Write `tests/test_vulcan.py` — socket mock, DNS fallback, subdomain brute
- [ ] Write `tests/test_titan.py` — mutation count, wordlist generation, analysis stats
- [ ] Write `tests/test_uranus.py` — ZIP-APK fixture, permission detection, secret extraction
- [ ] Write `tests/test_pluto.py` — keyword matching, cheatsheet content
- [ ] Write `tests/test_shell.py` — dispatcher, planet selection, arg building
- [ ] Add `pytest-cov` CI enforcement: fail build if coverage drops below 85%
- [ ] Add property-based tests with `hypothesis` for Venus encode/decode roundtrip

Acceptance: `pytest --cov=milkyway --cov-fail-under=85` passes in CI.

### 2.2.2 — Write-Up Generator

Auto-generate a polished CTF write-up from a Saturn session.

Tasks:
- [ ] `mw> saturn export <session_id> --format markdown` (already basic — expand)
- [ ] `mw> saturn export <session_id> --format html` — styled HTML with syntax highlighting
- [ ] Include: timeline of commands, outputs, annotated notes, final flag
- [ ] Template system: `~/.milkyway/templates/writeup.md.j2` (Jinja2)
- [ ] Auto-embed screenshots if a `screenshots/` folder exists in the challenge dir
- [ ] `mw> session share <id>` — publish to a pastebin/gist (optional, configurable)

Acceptance: A 10-command session exports a readable markdown write-up in under 1 second.

### 2.2.3 — Pluto Local LLM (Ollama)

Full Ollama integration so Pluto works offline with real AI.

Tasks:
- [ ] Auto-detect if Ollama is running at startup (non-blocking)
- [ ] `mw> pluto models` — list available Ollama models
- [ ] `mw> config set pluto.model phi3` — switch models
- [ ] Streaming output — print tokens as they arrive (not wait for full response)
- [ ] Context injection — automatically include recent Saturn log entries in the prompt
- [ ] `mw> pluto explain 42` — ask Pluto to explain what run #42 found
- [ ] Fallback chain: Ollama → OpenAI → keyword engine (graceful)

Acceptance: `mw> pluto suggest "I have a PCAP with HTTP traffic"` returns useful output with no internet if Ollama is running.

### 2.2.4 — Venus RSA Tools

Complete RSA attack suite (currently `rsa` command stub only).

Tasks:
- [ ] `venus rsa --n --e --c` — small e attack (low exponent), Wiener's attack, factorDB lookup
- [ ] `venus rsa --p --q --e --c` — direct CRT decryption when factors known
- [ ] `venus rsa --n --e` — try factoring n with sympy, check if small/smooth
- [ ] `venus padding-oracle --url --padding-error` — automated CBC padding oracle
- [ ] `venus ecb-detect --ciphertext` — detect ECB mode from repeated blocks
- [ ] Pure-Python RSA using `sympy` + `pycryptodome` — no openssl required

Acceptance: `venus rsa --n 3233 --e 17 --c 2790` outputs `m = 65` correctly.

### 2.2.5 — Saturn Session Improvements

- [ ] `mw> session list` — show all sessions with start/end time, run count
- [ ] `mw> session resume <id>` — set `MILKYWAY_SESSION` and continue tagging
- [ ] `mw> saturn bookmark <run_id> <label>` — flag important runs
- [ ] `mw> saturn search <regex>` — full-text search across all run outputs
- [ ] Run output stored with gzip compression (large ffuf outputs)
- [ ] `mw> saturn stats` — visual bar chart of runs by planet, by day

---

## v2.3.0 — GanymedePatch (+6 weeks)

**Theme:** Team collaboration, new domains, platform integrations.

### 2.3.1 — Team Sync (Shared Saturn)

Allow a team to share a Saturn database in real time.

Tasks:
- [ ] `mw> team init --git https://github.com/team/milkyway-db` — Git-backed shared DB
- [ ] `mw> team pull` — fetch teammates' runs
- [ ] `mw> team push` — push your runs
- [ ] `mw> team log` — merged timeline from all members
- [ ] `mw> team who` — show active members and last activity
- [ ] Conflict resolution: last-write-wins per run ID (IDs are UUIDs when in team mode)
- [ ] Optional: WebSocket-based live sync server (`mw server start`)

Acceptance: Two teammates run `team pull` and both see each other's Saturn logs within 30 seconds.

### 2.3.2 — CTF Platform Connectors

Auto-import challenges from major CTF platforms.

Tasks:
- [ ] `mw> challenge import picoctf --search "web"` — list + import picoCTF challenges
- [ ] `mw> challenge import htb <machine-name>` — HackTheBox machine import
- [ ] `mw> challenge import ctftime <event-id>` — CTFtime event challenge list
- [ ] Auto-download attached files into `challenge/files/`
- [ ] Auto-populate `notes.md` with challenge description
- [ ] `mw> challenge submit <flag>` — submit flag to platform (where API available)

Acceptance: `mw> challenge import picoctf --name "web gauntlet"` creates a complete workspace with files downloaded.

### 2.3.3 — New Planet: Cosmos (OSINT)

A dedicated OSINT planet for reconnaissance beyond network scanning.

Commands planned:
- [ ] `cosmos username <name>` — check username across 300+ sites (Sherlock integration)
- [ ] `cosmos email <addr>` — breach check, OSINT lookup
- [ ] `cosmos phone <number>` — carrier, region lookup
- [ ] `cosmos domain <domain>` — WHOIS + DNS + Shodan + certificate transparency
- [ ] `cosmos reverse-image <url>` — reverse image search
- [ ] `cosmos social <handle>` — aggregate social media presence
- [ ] `cosmos google-dork <target>` — generate and run Google dorks

Acceptance: `cosmos username kazim` returns results from 10+ sites in under 5 seconds.

### 2.3.4 — New Planet: Kraken (Stego Specialist)

Dedicated steganography planet beyond `earth steg`.

Commands planned:
- [ ] `kraken lsb <image>` — LSB analysis (pure Python with Pillow)
- [ ] `kraken dct <jpeg>` — DCT coefficient analysis (JPEG stego)
- [ ] `kraken audio <wav>` — audio steganography (LSB, spectogram)
- [ ] `kraken brute <image>` — steghide password brute-force
- [ ] `kraken zsteg <image>` — zsteg integration with Python fallback
- [ ] `kraken outguess <image>` — outguess stego detection

### 2.3.5 — Mercury Enhancements

- [ ] `mercury cors <url>` — CORS misconfiguration scanner
- [ ] `mercury lfi <url>` — LFI/path traversal tester with 30 payloads
- [ ] `mercury ssrf <url>` — SSRF probe with OOB detection
- [ ] `mercury xxe <url>` — XXE payload generator + tester
- [ ] `mercury waf <url>` — WAF fingerprinting
- [ ] `mercury subdomains <domain>` — passive subdomain discovery via crt.sh, HackerTarget

---

## v2.4.0 — CallistoEdge (+10 weeks)

**Theme:** Developer experience, extensibility, ecosystem.

### 2.4.1 — Plugin System

Allow anyone to add new planets or commands without touching core code.

Tasks:
- [ ] YAML manifest format for plugin definition:
  ```yaml
  name: cosmos
  version: 1.0.0
  planet: cosmos
  symbol: "🌌"
  color: bright_cyan
  commands:
    - name: username
      help: "Check username across sites"
      requires: [name]
  ```
- [ ] `mw> plugin install kazim-45/milkyway-cosmos` — GitHub-based plugin install
- [ ] `mw> plugin list` — show installed plugins
- [ ] `mw> plugin update cosmos` — update a plugin
- [ ] Plugin directory: `~/.milkyway/plugins/`
- [ ] Sandboxed execution — plugins run in subprocess, not in main process

### 2.4.2 — TUI Rewrite (Textual v1)

Full-screen interactive dashboard using latest Textual.

Screens planned:
- [ ] **Dashboard** — planet grid, recent Saturn runs, live stats
- [ ] **Saturn Log** — scrollable run table with diff viewer
- [ ] **Challenge Board** — Kanban: To-Do / In-Progress / Solved
- [ ] **Command Builder** — GUI form for any planet command
- [ ] **Live Output** — streaming output from any command in a split pane
- [ ] Mouse support: click to enter a planet, click to select a run

### 2.4.3 — VS Code Extension

`milkyway-vscode` extension for working inside VS Code.

Features:
- [ ] Sidebar: challenge list, Saturn log, current session
- [ ] Right-click on a file → "Analyze with MilkyWay Earth"
- [ ] Terminal integration: run `mw> mercury fuzz ...` from command palette
- [ ] Status bar: shows current challenge, active session, last Saturn run

### 2.4.4 — Shell Quality-of-Life

- [ ] `mw> history` — searchable run history (fzf-style fuzzy search)
- [ ] `mw> repeat` — re-run last command with same args
- [ ] Arrow-up history inside planet sub-shell cycles through that planet's history
- [ ] `mw> alias fuzz='mercury fuzz'` — user-defined command aliases
- [ ] `mw> macro <name>` — record + replay a sequence of commands
- [ ] Syntax highlighting of command output (e.g. found paths in green, errors in red)

---

## v3.0.0 — AndromedaCore (+4 months)

**Theme:** Scale, community, and intelligence.

### 3.0.1 — Web Dashboard

- [ ] Flask/FastAPI backend serving local web UI
- [ ] `mw server start` — launches dashboard at `http://localhost:8765`
- [ ] Visual Saturn timeline with filterable runs
- [ ] Challenge board with progress tracking
- [ ] Team activity feed
- [ ] Export reports as PDF

### 3.0.2 — Distributed Saturn

- [ ] Saturn as a proper server with REST API
- [ ] Multiple MilkyWay instances sync to one Saturn server
- [ ] Real-time WebSocket broadcast of new runs
- [ ] Role-based access: Captain (read/write), Member (write own), Viewer (read-only)

### 3.0.3 — Community Plugin Registry

- [ ] `plugins.milkyway-ctf.dev` — hosted plugin marketplace
- [ ] Submission, review, and version management
- [ ] 10+ community plugins as launch partners

### 3.0.4 — Machine Learning Assistance

- [ ] Train on CTF write-ups → suggest tools based on challenge category + keywords
- [ ] `pluto pattern <output>` — recognize patterns in tool output (e.g. "this looks like ECB")
- [ ] `pluto similar <challenge_desc>` — find similar past CTF challenges from write-up DB
- [ ] Anomaly detection in Saturn logs: "You ran this 10 times — try a different approach"

---

## Ongoing / Every Release

These items apply to every version:

### Testing
- [ ] Maintain ≥ 85% code coverage
- [ ] All pure-Python fallbacks must have unit tests with no external tools
- [ ] Integration tests: run a full CTF-style challenge end-to-end in CI
- [ ] Fuzz the command parser with `hypothesis`
- [ ] Test on Python 3.9, 3.10, 3.11, 3.12 (matrix in CI)

### Security
- [ ] Dependency audit with `safety check` on every PR
- [ ] No `shell=True` without explicit approval
- [ ] Pin all dependencies with `pip-compile`
- [ ] SBOM (Software Bill of Materials) generated on each release
- [ ] Responsible disclosure policy in `SECURITY.md`

### Documentation
- [ ] Keep `README.md` current with every feature change
- [ ] Update `CHANGELOG.md` on every release
- [ ] Write a blog post for every major milestone
- [ ] Record a demo video for each new planet
- [ ] Maintain a `CONTRIBUTING.md` with clear contribution workflow

### Distribution
- [ ] PyPI: publish on every tag via GitHub Actions (OIDC trusted publishing)
- [ ] Docker: multi-arch build (amd64 + arm64) on every release
- [ ] Homebrew tap: update formula sha256 on every release
- [ ] PPA: upload `.deb` to Launchpad on every release
- [ ] Kali Linux: submit for inclusion once stable 3.0.0 is released

### Community
- [ ] Respond to GitHub issues within 48 hours
- [ ] Monthly Discord office hours
- [ ] Track CTF results where teams used MilkyWay
- [ ] Maintain a `HALL_OF_FAME.md` with contributor shoutouts

---

## Success Metrics

| Metric | v2.2 | v2.3 | v3.0 |
|--------|------|------|------|
| GitHub stars | 100 | 500 | 1,000+ |
| Weekly active users | 50 | 200 | 1,000+ |
| Test coverage | 85% | 88% | 92% |
| Planets | 11 | 13 | 15+ |
| Commands | 60 | 75 | 100+ |
| Community plugins | 0 | 5 | 20+ |
| CTF teams using it | 3 | 15 | 50+ |
| Write-ups citing MilkyWay | 0 | 10 | 50+ |

---

## How to Contribute to the Roadmap

1. Open an issue tagged `roadmap` on GitHub
2. Describe the feature, its use case, and proposed implementation
3. Reference the milestone it belongs to
4. If accepted, it gets added to this file in the next PR

All roadmap changes go through `docs/` PRs and require at least one review.

---

*Last updated: v2.1.0 NebulaDawn · Maintained by Kazim (kazim-45)*
