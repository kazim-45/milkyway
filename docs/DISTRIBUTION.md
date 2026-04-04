# 🚀 MilkyWay — Distribution & Release Roadmap

This document walks you through making MilkyWay installable via every major package manager:
`pip install milkyway-ctf`, `apt install milkyway-ctf`, `brew install milkyway`, and more.

---

## 1. PyPI (pip install) — Immediate

This is already fully wired in `pyproject.toml`. Do this right now.

### Step 1 — Set up accounts
```bash
# Create a PyPI account at https://pypi.org/account/register/
# Enable 2FA (required for new packages)
# Generate an API token at https://pypi.org/manage/account/token/
```

### Step 2 — Install build tools
```bash
pip install build twine
```

### Step 3 — Build the distribution
```bash
cd milkyway/
python -m build
# Creates:
#   dist/milkyway_ctf-1.0.0-py3-none-any.whl
#   dist/milkyway-ctf-1.0.0.tar.gz
```

### Step 4 — Test on TestPyPI first
```bash
twine upload --repository testpypi dist/*
# Test install:
pip install --index-url https://test.pypi.org/simple/ milkyway-ctf
mw --version
```

### Step 5 — Publish to real PyPI
```bash
twine upload dist/*
# Users can now:
pip install milkyway-ctf
mw --version
```

### Step 6 — Automate releases with GitHub Actions
Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags: ["v*"]           # triggers on: git tag v1.0.1 && git push --tags

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write      # required for trusted publishing (no API key needed)
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

> ✅ After this, every `git tag v1.x.x && git push --tags` auto-publishes to PyPI.

---

## 2. GitHub Releases (zip/tarball) — Immediate

Users can `pip install` directly from GitHub even before PyPI:

```bash
pip install git+https://github.com/kazim-45/milkyway.git
pip install git+https://github.com/kazim-45/milkyway.git@v1.0.0
```

### Creating a release
```bash
git tag v1.0.0
git push origin v1.0.0
# Go to github.com/kazim-45/milkyway/releases/new
# Select tag v1.0.0
# Add release notes (paste CHANGELOG section)
# GitHub auto-attaches source zip + tarball
```

---

## 3. Docker (docker pull) — Next Week

### Step 1 — Set up GitHub Container Registry (GHCR)
Already in your Dockerfile. Add to `.github/workflows/docker.yml`:

```yaml
name: Build & Push Docker Image

on:
  push:
    tags: ["v*"]
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: kazim-45/milkyway

jobs:
  docker:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ghcr.io/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=raw,value=latest
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
```

Then users can:
```bash
docker pull ghcr.io/kazim-45/milkyway:latest
docker run -it --rm -v $(pwd):/workspace ghcr.io/kazim-45/milkyway
```

---

## 4. Homebrew (brew install) — 2–4 Weeks

Homebrew is the standard on macOS.

### Step 1 — Create a Homebrew tap repository
```bash
# Create a new GitHub repo named: homebrew-milkyway
# (The "homebrew-" prefix is required by Homebrew convention)
# Repo: github.com/kazim-45/homebrew-milkyway
```

### Step 2 — Create the Formula
Create `Formula/milkyway.rb` in `homebrew-milkyway`:

```ruby
class Milkyway < Formula
  desc "The Galactic CTF Orchestrator — modular, version-controlled CTF toolkit"
  homepage "https://github.com/kazim-45/milkyway"
  url "https://files.pythonhosted.org/packages/.../milkyway-ctf-1.0.0.tar.gz"
  sha256 "REPLACE_WITH_SHA256_FROM_PYPI"
  license "MIT"

  depends_on "python@3.11"

  resource "click" do
    url "https://files.pythonhosted.org/packages/.../click-8.1.7.tar.gz"
    sha256 "..."
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/.../rich-13.7.0.tar.gz"
    sha256 "..."
  end

  # Add all dependencies similarly (get sha256 from PyPI JSON API)

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/mw", "--version"
  end
end
```

### Step 3 — Users install via your tap
```bash
brew tap kazim-45/milkyway
brew install milkyway
mw --version
```

### Step 4 — Submit to Homebrew Core (optional, later)
Once you have 75+ GitHub stars and 30+ days of stable releases:
```bash
brew audit --new milkyway    # validate formula
brew test milkyway           # test locally
# Open PR to github.com/Homebrew/homebrew-core
```

---

## 5. apt / Debian Package — 1–2 Months

This makes `apt install milkyway-ctf` work on Debian/Ubuntu/Kali.

### Option A: Personal Package Archive (PPA) on Launchpad

1. Create a Launchpad account at https://launchpad.net/
2. Create a PPA: https://launchpad.net/~kazim-45/+activate-ppa
3. Package structure:

```
milkyway-ctf_1.0.0/
├── debian/
│   ├── control          # Package metadata
│   ├── rules            # Build instructions
│   ├── changelog        # Version history
│   ├── copyright        # License info
│   └── install          # File installation paths
```

`debian/control`:
```
Source: milkyway-ctf
Section: net
Priority: optional
Maintainer: Kazim <kazim@milkyway-ctf.dev>
Build-Depends: debhelper-compat (= 13), dh-python, python3-all, python3-setuptools
Standards-Version: 4.6.0
Homepage: https://github.com/kazim-45/milkyway
Rules-Requires-Root: no

Package: milkyway-ctf
Architecture: all
Depends: ${python3:Depends}, ${misc:Depends}, python3-click, python3-rich
Description: The Galactic CTF Orchestrator
 MilkyWay is a modular, version-controlled toolkit for CTF competitions.
 Organizes 50+ security tools into planets with a unified CLI, automatic
 Saturn version control, and an AI-powered assistant (Pluto).
```

```bash
# Build and upload:
debuild -S -sa
dput ppa:kazim-45/milkyway milkyway-ctf_1.0.0_source.changes

# Users then:
sudo add-apt-repository ppa:kazim-45/milkyway
sudo apt update
sudo apt install milkyway-ctf
```

### Option B: Kali Linux Repository (Best for CTF audience)
- Submit to https://gitlab.com/kalilinux/packages
- Follow Kali's packaging guide: https://www.kali.org/docs/development/intro-to-packaging-example/
- Your package would appear in `kali-tools-web`, `kali-tools-crypto`, etc.

---

## 6. Snap (snap install) — 1 Month

Snap works on all Linux distros.

### `snap/snapcraft.yaml`:
```yaml
name: milkyway-ctf
version: '1.0.0'
summary: The Galactic CTF Orchestrator
description: |
  MilkyWay is a modular, version-controlled toolkit for CTF competitions.
  Wraps 50+ security tools with a unified CLI, Saturn version control,
  and an AI-powered assistant.

grade: stable
confinement: classic       # 'classic' needed for filesystem access

base: core22

apps:
  milkyway:
    command: bin/milkyway
    plugs: [home, network, removable-media]
  mw:
    command: bin/mw
    plugs: [home, network, removable-media]

parts:
  milkyway:
    plugin: python
    source: .
    python-packages:
      - milkyway-ctf
```

```bash
# Publish:
snapcraft login
snapcraft
snapcraft upload milkyway-ctf_1.0.0_amd64.snap --release stable

# Users:
sudo snap install milkyway-ctf --classic
mw --version
```

---

## 7. One-Line Installer Script

Already at `scripts/install.sh`. Host it and users can:

```bash
curl -sSL https://raw.githubusercontent.com/kazim-45/milkyway/main/scripts/install.sh | bash
```

---

## Release Checklist (per version)

```
[ ] Update version in milkyway/__init__.py
[ ] Update CHANGELOG.md
[ ] Run full test suite: pytest tests/ -v
[ ] Commit + push: git push origin main
[ ] Tag: git tag v1.x.x && git push --tags
[ ] GitHub Actions auto-publishes to PyPI and GHCR
[ ] Update Homebrew formula sha256 (if tap exists)
[ ] Announce on Twitter @milkyway_ctf
[ ] Post on r/securityCTF and r/hacking
[ ] Update Discord community
```

---

## Version Numbering

MilkyWay follows [Semantic Versioning](https://semver.org/):

| Type | When | Example |
|------|------|---------|
| Patch (`x.x.Z`) | Bug fixes, docs | `1.0.1` |
| Minor (`x.Y.0`) | New commands, new planet features | `1.1.0` |
| Major (`X.0.0`) | Breaking CLI changes, new planets | `2.0.0` |

---

## Summary — Priority Order

| Priority | Channel | Reach | Effort |
|----------|---------|-------|--------|
| 🔴 Now   | PyPI (`pip install milkyway-ctf`) | Python users worldwide | 30 min |
| 🔴 Now   | GitHub Releases | All users | 10 min |
| 🟡 Week 1 | Docker (`docker pull`) | DevOps, Kali users | 1 hour |
| 🟡 Week 2 | Homebrew tap | macOS users | 2 hours |
| 🟢 Month 1 | Snap | All Linux distros | 2 hours |
| 🟢 Month 2 | apt/PPA or Kali repo | Debian/Ubuntu/Kali | 4 hours |
| 🔵 Later | Homebrew Core | Mainstream macOS | PR to homebrew-core |
| 🔵 Later | Kali Linux repo | CTF community | Kali packaging review |
