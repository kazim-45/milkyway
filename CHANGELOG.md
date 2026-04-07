# Changelog

All notable changes to MilkyWay are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

---

## [1.2.0] — 2026-04-06

### Added
- **♅ Uranus** — Mobile/IoT planet: `decompile`, `info`, `permissions`,
  `instrument`, `adb`, `strings`, `ssl-bypass`
- **🌋 Vulcan** — Network Recon & OSINT planet: `portscan`, `quickscan`,
  `whois`, `dns`, `subdomain`, `banner`
- **🪐 Titan** — Password Attacks planet: `brute`, `spray`, `wordlist`,
  `cewl`, `analyze`, `mutate`
- Dexter-style colored interactive shell with live task status display
  (`▶ Task` / `✓ Done` / `✗ Error` / `: Thinking...`)
- Per-planet color coding throughout the entire interface
- 87-entry tab completion (up from 65)
- 18 curated usage examples covering all 11 planets
- Full debian packaging (`debian/` directory)
- GitHub Actions CI/CD (`.github/workflows/ci.yml`)
- Docker image publish workflow (`.github/workflows/docker.yml`)
- `scripts/git_workflow.sh` — interactive branch/test/merge/release helper
- `scripts/publish_pypi.sh` — one-command PyPI publish
- `scripts/setup_apt_repo.sh` — GitHub Pages apt repo builder
- `docs/GIT_AND_RELEASE_GUIDE.md` — complete step-by-step workflow guide

### Changed
- Shell rewritten with `rich.Theme` and per-planet color palette
- Numbered menu now covers all 11 planets (was 8)
- Prompt shows `[challenge_name] mw>` with ANSI color (readline-safe)
- Spinner uses Unicode Braille frames for smooth animation

---

## [1.1.0] — 2026-04-04

### Added
- `mw` shorthand entry point (alias for `milkyway`)
- Interactive `mw>` shell with SET/Metasploit-style banner
- Numbered planet menu (type `1`–`8` to see planet sub-menus)
- Tab completion with readline and persistent history (`~/.milkyway/.history`)
- Dynamic prompt shows current challenge name when inside a workspace
- `scripts/install.sh` — one-line setup script
- `docs/DISTRIBUTION.md` — PyPI/apt/Homebrew/Snap roadmap

### Changed
- CLI restructured with consistent per-planet help text
- All planet groups use `short_help` with symbol + commands preview
- Saturn commands use `[bold cyan]` prefix markers (`[+]`, `[!]`, `[*]`)

---

## [1.0.0] — 2026-04-01

### Added
- **☿ Mercury** — Web Security: `fuzz`, `sql`, `request`, `headers`,
  `extract`, `scan`
- **♀ Venus** — Cryptography: `identify`, `hash`, `crack`, `encode`,
  `decode`, `xor`, `factor`
- **♁ Earth** — Forensics: `info`, `carve`, `strings`, `hexdump`,
  `steg`, `pcap`
- **♂ Mars** — Reverse Engineering: `disassemble`, `info`, `symbols`,
  `trace`, `r2`
- **♃ Jupiter** — Binary Exploitation: `checksec`, `rop`, `template`,
  `cyclic`
- **♆ Neptune** — Cloud & Misc: `jwt`, `cloud`, `url`
- **♇ Pluto** — AI Assistant: `suggest`, `analyze`, `cheatsheet`
- **🪐 Saturn** — Version Control: `log`, `diff`, `redo`, `status`,
  `annotate`, `export`
- Challenge workspace scaffolding (`challenge new`, `list`, `note`, `cd`)
- Session management (`session start`, `end`)
- SQLite-backed Saturn engine with WAL mode
- Pure-Python fallbacks for tools that are not installed
- `pyproject.toml` with `milkyway` + `mw` entry points
- Dockerfile with full Kali-based environment
- `docs/SATURN.md` and `docs/INSTALL.md`

[Unreleased]: https://github.com/kazim-45/milkyway/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/kazim-45/milkyway/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/kazim-45/milkyway/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/kazim-45/milkyway/releases/tag/v1.0.0
