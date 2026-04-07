#!/usr/bin/env bash
# scripts/setup_apt_repo.sh
# ─────────────────────────────────────────────────────────────────────────────
# Builds a .deb, creates a signed apt repository, and prepares it for
# hosting on GitHub Pages at: https://kazim-45.github.io/milkyway-apt/
#
# Prerequisites:
#   sudo apt install devscripts debhelper dh-python python3-all reprepro
#   gpg key already created and uploaded to keyserver.ubuntu.com
#
# Usage:
#   bash scripts/setup_apt_repo.sh [version]   e.g. bash scripts/setup_apt_repo.sh 1.2.0

set -euo pipefail

VERSION="${1:-1.2.0}"
PACKAGE="milkyway-ctf"
GPG_EMAIL="kazim@milkyway-ctf.dev"
REPO_DIR="$HOME/milkyway-apt-repo"
DIST="stable"

CYAN="\033[0;36m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

step() { echo -e "\n${CYAN}[*] $*${RESET}"; }
ok()   { echo -e "${GREEN}[+] $*${RESET}"; }
warn() { echo -e "${YELLOW}[!] $*${RESET}"; }
err()  { echo -e "${RED}[✗] $*${RESET}"; exit 1; }

# ── Check prerequisites ───────────────────────────────────────────────────────

step "Checking prerequisites..."
for cmd in gpg debuild dpkg-scanpackages gzip; do
    command -v "$cmd" &>/dev/null || err "$cmd not found. Install: sudo apt install devscripts dpkg-dev"
done
ok "All prerequisites found"

# ── Get GPG key ID ────────────────────────────────────────────────────────────

step "Looking up GPG key for $GPG_EMAIL..."
GPG_KEY_ID=$(gpg --list-keys --keyid-format LONG "$GPG_EMAIL" 2>/dev/null \
    | grep "pub" | awk '{print $2}' | cut -d'/' -f2 | head -1)

if [[ -z "$GPG_KEY_ID" ]]; then
    err "No GPG key found for $GPG_EMAIL. Create one with: gpg --gen-key"
fi
ok "GPG key: $GPG_KEY_ID"

# ── Build the .deb package ────────────────────────────────────────────────────

step "Building .deb package (v${VERSION})..."
cd "$(dirname "$0")/.."   # go to project root

# Update version in debian/changelog if needed
if ! grep -q "${VERSION}" debian/changelog; then
    warn "Version ${VERSION} not in debian/changelog — add it manually before publishing"
fi

debuild -b -uc -us 2>&1 | tail -20
DEB_FILE=$(ls "../${PACKAGE}_${VERSION}-"*"_all.deb" 2>/dev/null | head -1)

if [[ -z "$DEB_FILE" ]]; then
    err ".deb not found. Check build output above."
fi
ok "Built: $DEB_FILE"

# ── Create repository structure ───────────────────────────────────────────────

step "Creating apt repository structure at $REPO_DIR..."
mkdir -p "$REPO_DIR/pool/main"
mkdir -p "$REPO_DIR/dists/$DIST/main/binary-amd64"
mkdir -p "$REPO_DIR/dists/$DIST/main/binary-all"

cp "$DEB_FILE" "$REPO_DIR/pool/main/"
ok "Copied .deb to pool"

# ── Generate Packages index ───────────────────────────────────────────────────

step "Generating Packages index..."
cd "$REPO_DIR"

dpkg-scanpackages --arch amd64 pool/ /dev/null \
    > "dists/$DIST/main/binary-amd64/Packages"
gzip -k "dists/$DIST/main/binary-amd64/Packages"

dpkg-scanpackages --arch all pool/ /dev/null \
    > "dists/$DIST/main/binary-all/Packages"
gzip -k "dists/$DIST/main/binary-all/Packages"

ok "Packages index generated"

# ── Generate Release file ─────────────────────────────────────────────────────

step "Generating Release file..."
cat > "dists/$DIST/Release" << RELEASE_EOF
Origin: MilkyWay CTF Toolkit
Label: MilkyWay
Suite: $DIST
Codename: $DIST
Version: $VERSION
Architectures: amd64 all
Components: main
Description: MilkyWay CTF Toolkit — The Galactic CTF Orchestrator
Date: $(date -Ru)
RELEASE_EOF

# Append checksums
{
    echo "MD5Sum:"
    find "dists/$DIST" -name "Packages*" | while read f; do
        SIZE=$(wc -c < "$f")
        MD5=$(md5sum "$f" | cut -d' ' -f1)
        REL="${f#dists/$DIST/}"
        echo " $MD5 $SIZE $REL"
    done

    echo "SHA256:"
    find "dists/$DIST" -name "Packages*" | while read f; do
        SIZE=$(wc -c < "$f")
        SHA=$(sha256sum "$f" | cut -d' ' -f1)
        REL="${f#dists/$DIST/}"
        echo " $SHA $SIZE $REL"
    done
} >> "dists/$DIST/Release"

ok "Release file generated"

# ── Sign the Release file ─────────────────────────────────────────────────────

step "Signing Release with GPG key $GPG_KEY_ID..."
gpg --default-key "$GPG_KEY_ID" \
    --armor --detach-sign \
    --output "dists/$DIST/Release.gpg" \
    "dists/$DIST/Release"

gpg --default-key "$GPG_KEY_ID" \
    --armor --clearsign \
    --output "dists/$DIST/InRelease" \
    "dists/$DIST/Release"

ok "Repository signed"

# ── Export public key ─────────────────────────────────────────────────────────

step "Exporting public key..."
gpg --armor --export "$GPG_EMAIL" > "$REPO_DIR/milkyway.gpg"
ok "Public key exported to $REPO_DIR/milkyway.gpg"

# ── Create GitHub Pages repo ──────────────────────────────────────────────────

step "Setting up GitHub Pages repository..."
cd "$REPO_DIR"

if [[ ! -d ".git" ]]; then
    git init
    git checkout -b gh-pages
    cat > README.md << 'README_EOF'
# MilkyWay APT Repository

Add this repository to install MilkyWay via apt:

```bash
curl -fsSL https://kazim-45.github.io/milkyway-apt/milkyway.gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/milkyway.gpg

echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/milkyway.gpg] \
  https://kazim-45.github.io/milkyway-apt stable main" \
  | sudo tee /etc/apt/sources.list.d/milkyway.list

sudo apt update
sudo apt install milkyway-ctf
```
README_EOF
fi

git add .
git commit -m "apt repo: milkyway-ctf v${VERSION}"

echo ""
ok "Repository ready at: $REPO_DIR"
echo ""
echo "  Next steps:"
echo "  1. Create GitHub repo: github.com/kazim-45/milkyway-apt"
echo "  2. Push:"
echo "     cd $REPO_DIR"
echo "     git remote add origin https://github.com/kazim-45/milkyway-apt.git"
echo "     git push -u origin gh-pages"
echo "  3. Enable GitHub Pages: Settings → Pages → Source: gh-pages"
echo ""
echo "  Users install with:"
echo "  curl -fsSL https://kazim-45.github.io/milkyway-apt/milkyway.gpg \\"
echo "    | sudo gpg --dearmor -o /etc/apt/keyrings/milkyway.gpg"
echo "  echo 'deb [arch=amd64 signed-by=/etc/apt/keyrings/milkyway.gpg] \\"
echo "    https://kazim-45.github.io/milkyway-apt stable main' \\"
echo "    | sudo tee /etc/apt/sources.list.d/milkyway.list"
echo "  sudo apt update && sudo apt install milkyway-ctf"
