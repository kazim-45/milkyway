# MilkyWay — Complete Release Guide
## Git Branching · Testing · Merging · pip install · apt install

---

## PART 1 — ONE-TIME SETUP

### 1.1 Initialize the repo (do this once)

```bash
cd ~/milkyway                      # wherever you extracted the zip

git init
git add .
git commit -m "🌌 feat: MilkyWay v1.2.0 — 11-planet CTF orchestrator"

# Connect to GitHub (create the repo on github.com first, then:)
git remote add origin https://github.com/kazim-45/milkyway.git
git branch -M main
git push -u origin main
```

### 1.2 Set your identity (once per machine)

```bash
git config --global user.name  "Kazim"
git config --global user.email "kazim@milkyway-ctf.dev"
```

---

## PART 2 — BRANCH WORKFLOW (do this for every feature or fix)

### The rule: never commit directly to main

```
main  ──────●──────────────────────────●──── production
             \                        /
  test/v1.2   ●──●──●──●──●──●──●──●   feature work + testing
```

### 2.1 Create a test branch

```bash
# Always branch off the latest main
git checkout main
git pull origin main

# Create and switch to test branch
git checkout -b test/v1.2.0
```

**Branch naming convention:**

| Type | Pattern | Example |
|------|---------|---------|
| Testing / release candidate | `test/vX.Y.Z` | `test/v1.2.0` |
| New feature | `feat/description` | `feat/uranus-ssl-bypass` |
| Bug fix | `fix/description` | `fix/saturn-diff-crash` |
| Documentation | `docs/description` | `docs/apt-guide` |
| Hotfix (urgent) | `hotfix/description` | `hotfix/banner-encoding` |

### 2.2 Make your changes on the branch

```bash
# Edit files, add new planets, fix bugs...
vim milkyway/cli/planets/uranus.py

# Stage and commit incrementally
git add milkyway/cli/planets/uranus.py
git commit -m "feat(uranus): add ssl-bypass command with Frida fallback"

git add milkyway/shell.py
git commit -m "ui(shell): Dexter-style coloured task status lines"

# Push the branch to GitHub (others can review it)
git push -u origin test/v1.2.0
```

**Write good commit messages:**
```
feat(planet):   new command or planet
fix(core):      bug fix in core module
test(saturn):   add/update tests
docs(readme):   documentation update
ui(shell):      visual/interface change
chore(build):   pyproject, CI, packaging
```

---

## PART 3 — RUNNING MILKYWAY ON THE TEST BRANCH

### 3.1 Install in editable mode (changes take effect immediately)

```bash
# While on the test branch:
git checkout test/v1.2.0

# Create a virtual environment (keeps your system Python clean)
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Install MilkyWay in editable mode + dev dependencies
pip install -e ".[dev]"
```

Now every edit to `milkyway/` is instantly live — no reinstall needed.

### 3.2 Run the interactive shell

```bash
mw                               # interactive mw> shell (SET-style)
milkyway                         # same thing, longer alias
```

### 3.3 Run individual planet commands

```bash
# Web security
mw mercury fuzz http://target.com/FUZZ
mw mercury headers http://target.com

# Crypto
mw venus identify '5f4dcc3b5aa765d61d8327deb882cf99'
mw venus decode 'aGVsbG8=' --enc base64

# Forensics
mw earth strings ./suspicious_file --grep flag
mw earth info ./image.png

# Reverse engineering
mw mars info ./binary

# Binary exploitation
mw jupiter cyclic 200
mw jupiter checksec ./binary

# Mobile/IoT (NEW)
mw uranus decompile ./app.apk
mw uranus permissions ./app.apk

# Network recon (NEW)
mw vulcan quickscan 10.10.10.10
mw vulcan dns example.com --type MX

# Password attacks (NEW)
mw titan wordlist --charset digits --min 4 --max 4 -o pins.txt
mw titan mutate names.txt

# AI assistant
mw pluto suggest "I found a base64 string in the response"

# Version control
mw saturn log
mw saturn status
```

### 3.4 Run the full test suite

```bash
# From the project root (with venv active):
pytest tests/ -v

# With coverage report:
pytest tests/ -v --cov=milkyway --cov-report=term-missing

# Run a single test file:
pytest tests/test_saturn.py -v
pytest tests/test_venus.py -v

# Run a single test:
pytest tests/test_venus.py::test_hash_md5 -v
```

**Expected output when all tests pass:**
```
tests/test_saturn.py::test_record_and_retrieve_run   PASSED
tests/test_saturn.py::test_failed_run                PASSED
tests/test_venus.py::test_hash_md5                   PASSED
tests/test_venus.py::test_encode_base64              PASSED
... (50+ tests)
========== 52 passed in 1.24s ==========
```

### 3.5 Check tool availability

```bash
mw tools           # show which external tools are found
mw tools --install # show install hints for missing ones
```

---

## PART 4 — MERGING BACK TO MAIN

### 4.1 Make sure all tests pass first

```bash
# On the test branch:
pytest tests/ -v                       # must be all green
```

### 4.2 Merge via Pull Request (recommended — GitHub)

```bash
# Push your branch
git push origin test/v1.2.0

# On GitHub:
# 1. Go to github.com/kazim-45/milkyway
# 2. Click "Compare & pull request" (appears automatically)
# 3. Set base: main  ←  compare: test/v1.2.0
# 4. Write a description of changes
# 5. Click "Create pull request"
# 6. Review the diff, then "Merge pull request"
# 7. Delete the branch on GitHub after merging
```

### 4.3 Merge locally (if you're working solo)

```bash
# Switch to main
git checkout main
git pull origin main                    # make sure it's up to date

# Merge (fast-forward if no conflicts, else create a merge commit)
git merge test/v1.2.0 --no-ff -m "merge: test/v1.2.0 → main (MilkyWay v1.2.0)"

# Push to GitHub
git push origin main

# Delete the test branch locally
git branch -d test/v1.2.0

# Delete it on GitHub too
git push origin --delete test/v1.2.0
```

### 4.4 Tag the release

```bash
git checkout main
git tag -a v1.2.0 -m "MilkyWay v1.2.0 — 11 planets, Dexter-style UI"
git push origin v1.2.0
```

This tag triggers the GitHub Actions workflow to auto-publish to PyPI (see Part 5).

---

## PART 5 — pip install milkyway-ctf (PyPI)

### 5.1 One-time setup

```bash
# Install build tools
pip install build twine

# Create PyPI account:   https://pypi.org/account/register/
# Enable 2FA (required for new packages)
# Create API token:      https://pypi.org/manage/account/token/
#   → Scope: "Entire account" for first publish, then switch to project-scoped

# Save token to ~/.pypirc  (never commit this file)
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

### 5.2 Update version before publishing

Edit `milkyway/__init__.py`:
```python
__version__ = "1.2.0"      # bump this
```

Edit `pyproject.toml`:
```toml
[project]
version = "1.2.0"           # bump this too — must match __init__.py
```

### 5.3 Build the distribution

```bash
cd ~/milkyway
python -m build
```

This creates:
```
dist/
  milkyway_ctf-1.2.0-py3-none-any.whl    ← wheel (fast install)
  milkyway_ctf-1.2.0.tar.gz              ← source distribution
```

### 5.4 Test on TestPyPI first (always)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test the install in a fresh venv
python3 -m venv /tmp/mw-test
source /tmp/mw-test/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            milkyway-ctf

# Verify
mw --version          # should print: MilkyWay 1.2.0
mw venus hash hello   # should print md5 hash
mw saturn status      # should show DB path

deactivate
rm -rf /tmp/mw-test
```

### 5.5 Publish to real PyPI

```bash
twine upload dist/*
```

**Users can now install with:**
```bash
pip install milkyway-ctf
mw --version
```

### 5.6 Automate with GitHub Actions (publish on every tag)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - "v*"          # triggers on: git tag v1.2.0 && git push --tags

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v

  publish:
    needs: test          # only publish if tests pass
    runs-on: ubuntu-latest
    permissions:
      id-token: write    # required for trusted publishing (no API key)
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # No password needed — uses OIDC trusted publishing
        # Set up at: https://pypi.org/manage/project/milkyway-ctf/settings/publishing/
```

**After this workflow exists:**
```bash
git tag v1.2.0
git push origin v1.2.0
# → GitHub runs tests → publishes to PyPI automatically
```

To set up Trusted Publishing (no API key needed):
1. Go to https://pypi.org/manage/project/milkyway-ctf/settings/publishing/
2. Add publisher: GitHub → `kazim-45/milkyway` → workflow `publish.yml` → env `pypi`

---

## PART 6 — sudo apt install milkyway-ctf

`apt install` requires a Debian/Ubuntu package repository. There are three ways
to do this, in order of effort:

---

### Option A: Personal Package Archive on Launchpad (fastest, ~2 hours)

This is the easiest path. Users add your PPA with one command, then `apt install` works.

#### Step 1 — Create a Launchpad account
Go to https://launchpad.net/ → Sign in with Ubuntu One account (or create one).

#### Step 2 — Create a PPA
Go to: `https://launchpad.net/~kazim-45/+activate-ppa`
- Name: `milkyway`
- Display name: `MilkyWay CTF Toolkit`
- Click "Activate"

Your PPA URL will be: `ppa:kazim-45/milkyway`

#### Step 3 — Set up GPG signing key

```bash
# Install tools
sudo apt install devscripts dh-python python3-all python3-setuptools debhelper

# Generate a GPG key if you don't have one
gpg --gen-key
# Choose: RSA 4096, no expiry, use your Launchpad email

# Get the key fingerprint
gpg --list-keys

# Upload it to Ubuntu's keyserver
gpg --keyserver keyserver.ubuntu.com --send-keys YOUR_KEY_FINGERPRINT

# Import it to Launchpad
# Go to: https://launchpad.net/~kazim-45/+editpgpkeys
# Paste your fingerprint and click "Import Key"
```

#### Step 4 — Create Debian packaging files

Inside your project, create a `debian/` directory:

```
milkyway/
└── debian/
    ├── changelog
    ├── control
    ├── copyright
    ├── install
    └── rules
```

**`debian/control`:**
```
Source: milkyway-ctf
Section: net
Priority: optional
Maintainer: Kazim <kazim@milkyway-ctf.dev>
Build-Depends:
 debhelper-compat (= 13),
 dh-python,
 python3-all,
 python3-setuptools,
 python3-click,
 python3-rich
Standards-Version: 4.6.2
Homepage: https://github.com/kazim-45/milkyway
Rules-Requires-Root: no

Package: milkyway-ctf
Architecture: all
Depends:
 ${python3:Depends},
 ${misc:Depends},
 python3-click (>= 8.1),
 python3-rich (>= 13.0),
 python3-yaml,
 python3-requests
Description: The Galactic CTF Orchestrator
 MilkyWay is a modular, version-controlled toolkit for Capture The Flag
 competitions and hackathons. It wraps 50+ security tools into a unified
 CLI with automatic Saturn version control, 11 security planets, and an
 AI-powered assistant (Pluto).
 .
 Planets: Mercury (Web), Venus (Crypto), Earth (Forensics), Mars (RevEng),
 Jupiter (Binary Exploitation), Neptune (Cloud), Uranus (Mobile/IoT),
 Vulcan (Network Recon), Titan (Password Attacks), Pluto (AI), Saturn (VCS).
```

**`debian/changelog`:**
```
milkyway-ctf (1.2.0-1) noble; urgency=medium

  * Initial Debian/Ubuntu packaging
  * 11 planets: Mercury, Venus, Earth, Mars, Jupiter, Neptune,
    Uranus, Vulcan, Titan, Pluto, Saturn
  * Dexter-style colored interactive shell

 -- Kazim <kazim@milkyway-ctf.dev>  Mon, 06 Apr 2026 00:00:00 +0000
```

**`debian/rules`:**
```makefile
#!/usr/bin/make -f
%:
	dh $@ --with python3 --buildsystem=pybuild

override_dh_auto_install:
	dh_auto_install
	# Ensure both entry points are installed
	install -m 755 debian/milkyway-ctf/usr/bin/milkyway \
	              debian/milkyway-ctf/usr/bin/mw 2>/dev/null || true
```

**`debian/install`:**
```
milkyway/ usr/lib/python3/dist-packages/
```

**`debian/copyright`:**
```
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: milkyway-ctf
Upstream-Contact: kazim@milkyway-ctf.dev
Source: https://github.com/kazim-45/milkyway

Files: *
Copyright: 2024-2026 Kazim <kazim@milkyway-ctf.dev>
License: MIT
```

#### Step 5 — Build the source package

```bash
cd ~/milkyway

# Build source package (signed with your GPG key)
debuild -S -sa

# This creates in the parent directory:
#   milkyway-ctf_1.2.0-1.dsc
#   milkyway-ctf_1.2.0-1.tar.gz
#   milkyway-ctf_1.2.0-1_source.changes
```

#### Step 6 — Upload to Launchpad

```bash
# Upload to your PPA
dput ppa:kazim-45/milkyway ../milkyway-ctf_1.2.0-1_source.changes
```

Launchpad will email you when the build completes (usually 10–30 minutes).

#### Step 7 — Users install with:

```bash
sudo add-apt-repository ppa:kazim-45/milkyway
sudo apt update
sudo apt install milkyway-ctf

# Then use:
mw --version
mw
```

---

### Option B: Self-hosted apt repository (full control)

Use this if you want `apt install milkyway-ctf` without a PPA — hosted on
GitHub Pages or your own server.

#### Step 1 — Build the .deb package

```bash
cd ~/milkyway

# Build binary + source package
debuild -b -uc -us     # -uc/-us = unsigned for local testing

# Creates: ../milkyway-ctf_1.2.0-1_all.deb
```

#### Step 2 — Set up the repository structure

```bash
mkdir -p ~/apt-repo/{pool/main,dists/stable/main/binary-amd64}

# Copy your .deb file
cp ../milkyway-ctf_1.2.0-1_all.deb ~/apt-repo/pool/main/

# Generate Packages index
cd ~/apt-repo
dpkg-scanpackages --arch amd64 pool/ > dists/stable/main/binary-amd64/Packages
gzip -k dists/stable/main/binary-amd64/Packages

# Generate Release file
cat > dists/stable/Release << EOF
Origin: MilkyWay CTF
Label: MilkyWay
Suite: stable
Codename: stable
Architectures: amd64 all
Components: main
Description: MilkyWay CTF Toolkit repository
EOF

# Sign the Release file
gpg --armor --detach-sign \
    --output dists/stable/Release.gpg \
    dists/stable/Release

gpg --armor --clearsign \
    --output dists/stable/InRelease \
    dists/stable/Release
```

#### Step 3 — Host on GitHub Pages

```bash
# Push the apt-repo directory to a GitHub Pages branch
cd ~/apt-repo
git init
git checkout -b gh-pages
git add .
git commit -m "apt repo: milkyway-ctf 1.2.0"
git remote add origin https://github.com/kazim-45/milkyway-apt.git
git push -u origin gh-pages

# Enable Pages in repo Settings → Pages → Source: gh-pages branch
# Your repo will be at: https://kazim-45.github.io/milkyway-apt/
```

#### Step 4 — Export your GPG public key for users

```bash
gpg --armor --export kazim@milkyway-ctf.dev > milkyway.gpg
# Host this file at: https://kazim-45.github.io/milkyway-apt/milkyway.gpg
```

#### Step 5 — Users install with:

```bash
# Download and trust the signing key
curl -fsSL https://kazim-45.github.io/milkyway-apt/milkyway.gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/milkyway.gpg

# Add the repository
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/milkyway.gpg] \
  https://kazim-45.github.io/milkyway-apt stable main" \
  | sudo tee /etc/apt/sources.list.d/milkyway.list

# Install
sudo apt update
sudo apt install milkyway-ctf
mw --version
```

---

### Option C: Kali Linux Official Repository (highest reach, 1–2 months)

Getting into Kali's repo means every Kali Linux install in the world can
`sudo apt install milkyway-ctf`. This is the ultimate goal.

1. Follow Kali's packaging guide:
   https://www.kali.org/docs/development/intro-to-packaging-example/

2. Submit a package request:
   https://bugs.kali.org → "New Package" bug report

3. Requirements before submitting:
   - Tool must be working and useful for penetration testing
   - Clean Debian packaging (`lintian` passes with no errors)
   - Active GitHub repo with 50+ stars recommended
   - Already on PyPI

4. Timeline: usually 1–3 months from submission to inclusion.

5. Once accepted, every Kali user can:
   ```bash
   sudo apt install milkyway-ctf
   ```

---

## PART 7 — COMPLETE WORKFLOW CHEATSHEET

### Daily development loop

```bash
# 1. Start work on a new branch
git checkout main && git pull
git checkout -b feat/my-feature

# 2. Make changes, commit often
vim milkyway/cli/planets/mercury.py
git add -p                         # stage hunks interactively
git commit -m "feat(mercury): add rate-limit bypass option"

# 3. Run tests before pushing
pytest tests/ -v                   # all green?

# 4. Push branch
git push -u origin feat/my-feature

# 5. Open Pull Request on GitHub, review, merge

# 6. Clean up
git checkout main
git pull
git branch -d feat/my-feature
```

### Release loop

```bash
# 1. Bump version
vim milkyway/__init__.py           # __version__ = "1.2.1"
vim pyproject.toml                 # version = "1.2.1"
git commit -am "chore: bump version to 1.2.1"

# 2. Tag and push
git tag v1.2.1
git push origin main --tags        # triggers GitHub Actions → PyPI

# 3. Build .deb and upload to PPA
debuild -S -sa
dput ppa:kazim-45/milkyway ../milkyway-ctf_1.2.1-1_source.changes

# 4. Announce on Twitter/Discord
```

### Useful git commands

```bash
git log --oneline --graph --all    # visual branch history
git diff main...test/v1.2.0        # what changed vs main
git stash                          # save uncommitted work temporarily
git stash pop                      # restore stashed work
git cherry-pick <commit-hash>      # copy one commit to current branch
git rebase main                    # replay your branch on top of latest main
```

---

## PART 8 — SUMMARY OF INSTALL METHODS

| Method | Command | Audience | Status |
|--------|---------|----------|--------|
| pip (recommended) | `pip install milkyway-ctf` | Python users | Ready now |
| git (latest dev) | `pip install git+https://github.com/kazim-45/milkyway` | Developers | Ready now |
| Docker | `docker run -it ghcr.io/kazim-45/milkyway` | Any OS | After CI setup |
| Homebrew | `brew install kazim-45/milkyway/milkyway` | macOS | After tap setup |
| apt (PPA) | `sudo add-apt-repository ppa:kazim-45/milkyway && sudo apt install milkyway-ctf` | Ubuntu/Kali | ~2 hours |
| apt (self-hosted) | `sudo apt install milkyway-ctf` (after adding source) | Linux | ~1 day |
| apt (Kali official) | `sudo apt install milkyway-ctf` | All Kali users | 1–3 months |
