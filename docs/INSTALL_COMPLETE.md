# MilkyWay — Complete Installation Guide
## pip install · apt install · From Source · Docker

---

## Quick Reference

| Method | Command | Works on | Time |
|--------|---------|----------|------|
| **pip** | `pip install milkyway-ctf` | Any OS with Python 3.9+ | 2 min |
| **apt (PPA)** | `sudo apt install milkyway-ctf` | Ubuntu / Kali (after PPA setup) | 1 min |
| **Docker** | `docker run -it ghcr.io/kazim-45/milkyway` | Any OS with Docker | 3 min |
| **One-liner** | `curl ... \| bash` | Linux / macOS | 3 min |
| **Source** | `git clone ... && pip install -e .` | Any OS | 5 min |

---

## Method 1 — pip install (Recommended)

`pip install milkyway-ctf` pulls MilkyWay **plus every Python security library** in one command:
`capstone`, `pwntools`, `ROPgadget`, `pycryptodome`, `androguard`, `dnspython`, `PyJWT`,
`paramiko`, `beautifulsoup4`, `sympy`, `pillow`, `passlib`, `openai`, and more.

**Zero "tool not found" errors.** Every command has a pure-Python fallback.

```bash
# Recommended: use a virtual environment
python3 -m venv ~/.milkyway-env
source ~/.milkyway-env/bin/activate

pip install milkyway-ctf

mw --version     # MilkyWay 2.1.0 | The Galactic CTF Orchestrator
mw               # Launch interactive shell
```

### Add to PATH permanently

```bash
echo 'export PATH="$HOME/.milkyway-env/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Tab completion

```bash
# Bash
_MILKYWAY_COMPLETE=bash_source mw > ~/.milkyway_complete.bash
echo 'source ~/.milkyway_complete.bash' >> ~/.bashrc
source ~/.bashrc

# Zsh
_MILKYWAY_COMPLETE=zsh_source mw > ~/.milkyway_complete.zsh
echo 'source ~/.milkyway_complete.zsh' >> ~/.zshrc
source ~/.zshrc
```

### Upgrade

```bash
pip install --upgrade milkyway-ctf
```

### With optional system tools (full power)

```bash
# Kali / Ubuntu / Debian
sudo apt install -y nmap whois dnsutils binutils file xxd exiftool \
    binwalk steghide tshark sqlmap hashcat john radare2 strace ltrace \
    gdb checksec hydra medusa crunch apktool

# Go tools (ffuf, nuclei)
go install github.com/ffuf/ffuf/v2@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
```

---

## Method 2 — apt install (Ubuntu / Kali)

### Option A — Launchpad PPA (Recommended)

```bash
sudo add-apt-repository ppa:kazim-45/milkyway
sudo apt update
sudo apt install milkyway-ctf
```

#### Publishing to the PPA (for Kazim)

**One-time GPG + Launchpad setup:**
```bash
# Install packaging tools
sudo apt install devscripts debhelper dh-python python3-all python3-setuptools

# Generate GPG key (use your Launchpad email)
gpg --gen-key

# Get key fingerprint
gpg --list-keys --keyid-format LONG kazim@milkyway-ctf.dev

# Upload to Ubuntu keyserver
gpg --keyserver keyserver.ubuntu.com --send-keys YOUR_FINGERPRINT

# Go to https://launchpad.net/~kazim-45/+activate-ppa → create PPA named "milkyway"
# Go to https://launchpad.net/~kazim-45/+editpgpkeys → import your fingerprint
```

**Per-release upload:**
```bash
cd milkyway/

# Update debian/changelog with new version
dch -v 2.1.0-1 "Release v2.1.0: planet sub-shell, numbered commands"

# Build signed source package
debuild -S -sa

# Upload to PPA
dput ppa:kazim-45/milkyway ../milkyway-ctf_2.1.0-1_source.changes

# Launchpad builds + publishes in ~20 minutes
# Users can then: sudo apt install milkyway-ctf
```

**To support multiple Ubuntu versions (noble/jammy/focal):**
```bash
# Build once per series, changing the changelog target
debuild -S -sa   # for noble (24.04)
sed -i 's/) noble;/) jammy;/' debian/changelog
debuild -S -sa   # for jammy (22.04)
# Upload all .changes files with dput
```

### Option B — Self-Hosted apt Repository (GitHub Pages)

```bash
# Build and create signed repo structure
bash scripts/setup_apt_repo.sh 2.1.0

# Push to GitHub Pages
cd ~/milkyway-apt-repo
git remote add origin https://github.com/kazim-45/milkyway-apt.git
git push -u origin gh-pages
# Enable Pages in repo settings → Source: gh-pages
```

Users install with:
```bash
curl -fsSL https://kazim-45.github.io/milkyway-apt/milkyway.gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/milkyway.gpg

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/milkyway.gpg] \
  https://kazim-45.github.io/milkyway-apt stable main" \
  | sudo tee /etc/apt/sources.list.d/milkyway.list

sudo apt update && sudo apt install milkyway-ctf
```

### Option C — Kali Linux Official Repository

Getting into Kali means every Kali user worldwide gets `apt install milkyway-ctf` with no setup.

Requirements:
- Stable PyPI releases (done)
- Clean Debian packaging — `lintian` passes with 0 errors (done)
- 50+ GitHub stars (get there first)
- Active maintenance history

Submission:
```bash
# 1. Run lintian
lintian ../milkyway-ctf_2.1.0-1.dsc

# 2. Follow Kali packaging guide
#    https://www.kali.org/docs/development/intro-to-packaging-example/

# 3. Submit bug report at https://bugs.kali.org
#    Category: "New Tool Requests"
#    Include: description, upstream URL, why it belongs in Kali
```

Timeline: 1–3 months after a complete submission.

---

## Method 3 — One-Line Installer

```bash
# Basic install (pip-based)
curl -sSL https://raw.githubusercontent.com/kazim-45/milkyway/main/scripts/install.sh | bash

# Full install with system tools (Linux only, requires sudo)
curl -sSL https://raw.githubusercontent.com/kazim-45/milkyway/main/scripts/install.sh | bash -s -- --full
```

---

## Method 4 — Docker

```bash
# Run (auto-pulls if not cached)
docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway

# Specific version
docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway:2.1.0

# Build locally
git clone https://github.com/kazim-45/milkyway
cd milkyway
docker build -t milkyway .
docker run -it --rm -v $(pwd):/workspace milkyway
```

The Docker image includes everything: all Python libs, nmap, hashcat, ffuf, nuclei,
binutils, radare2, tshark, steghide, apktool, hydra, crunch, rockyou.txt.

---

## Method 5 — From Source

```bash
git clone https://github.com/kazim-45/milkyway
cd milkyway
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # editable — changes take effect immediately
mw --version
pytest tests/ -v
```

---

## Making pip install Work — PyPI Publishing

### One-time setup

```bash
pip install build twine

# Create PyPI account → enable 2FA → create API token
# Save to ~/.pypirc (chmod 600)
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE

[testpypi]
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
EOF
chmod 600 ~/.pypirc
```

### Manual release

```bash
# 1. Bump version in both places
vim milkyway/__init__.py    # __version__ = "2.1.0"
vim pyproject.toml          # version = "2.1.0"
git commit -am "chore: bump version to 2.1.0"

# 2. Run tests
pytest tests/ -v

# 3. Build
python -m build
# Creates: dist/milkyway_ctf-2.1.0-py3-none-any.whl
#          dist/milkyway_ctf-2.1.0.tar.gz

# 4. Test on TestPyPI first
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            milkyway-ctf==2.1.0
mw --version   # confirm: MilkyWay 2.1.0

# 5. Publish to real PyPI
twine upload dist/*

# 6. Tag and push
git tag v2.1.0
git push origin v2.1.0
```

### Automated via GitHub Actions (recommended)

Set up OIDC Trusted Publishing — no API keys in secrets:

1. Go to `https://pypi.org/manage/project/milkyway-ctf/settings/publishing/`
2. Add a publisher:
   - GitHub → repository: `kazim-45/milkyway`
   - Workflow: `ci.yml`
   - Environment: `pypi`

Now every tag push auto-publishes:
```bash
git tag v2.1.0
git push origin v2.1.0
# → GitHub Actions: tests → build → publish to PyPI → GitHub Release
```

---

## Verification

After any installation:

```bash
mw --version                    # MilkyWay 2.1.0
mw venus hash hello             # 5d41402abc4b2a76b9719d911017c592
mw venus decode 'aGVsbG8='     # hello
mw jupiter cyclic 50            # 50-char De Bruijn pattern
mw saturn status                # DB path + stats (no DB errors)
mw tools                        # Tool availability table
```

All six must work with zero external tools installed.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `mw: command not found` | `export PATH="$HOME/.milkyway-env/bin:$PATH"` |
| `ModuleNotFoundError` | `pip install milkyway-ctf --force-reinstall` |
| `Permission denied` | Use venv — never `sudo pip` |
| Broken colors | `export TERM=xterm-256color` |
| Saturn DB locked | `rm ~/.milkyway/global.db-wal ~/.milkyway/global.db-shm` |

---

*For help: [GitHub Issues](https://github.com/kazim-45/milkyway/issues) · [Discord](https://discord.gg/milkyway)*
