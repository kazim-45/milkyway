#!/usr/bin/env bash
# scripts/publish_pypi.sh
# ─────────────────────────────────────────────────────────────────────────────
# Builds and publishes MilkyWay to PyPI (or TestPyPI).
# Run from the project root.
#
# Usage:
#   bash scripts/publish_pypi.sh           → publish to real PyPI
#   bash scripts/publish_pypi.sh --test    → publish to TestPyPI first

set -euo pipefail

TEST_MODE=0
[[ "${1:-}" == "--test" ]] && TEST_MODE=1

CYAN="\033[0;36m"; GREEN="\033[0;32m"
YELLOW="\033[0;33m"; RED="\033[0;31m"; RESET="\033[0m"
step() { echo -e "\n${CYAN}[*] $*${RESET}"; }
ok()   { echo -e "${GREEN}[+] $*${RESET}"; }
warn() { echo -e "${YELLOW}[!] $*${RESET}"; }
err()  { echo -e "${RED}[✗] $*${RESET}"; exit 1; }

# ── Check we're in the project root ──────────────────────────────────────────

[[ -f "pyproject.toml" ]] || err "Run this script from the project root (~/milkyway/)"

# ── Read current version ──────────────────────────────────────────────────────

VERSION=$(python3 -c "
import re
text = open('pyproject.toml').read()
m = re.search(r'version\s*=\s*\"([^\"]+)\"', text)
print(m.group(1))
")
step "Publishing milkyway-ctf v${VERSION}..."

# ── Check tools ───────────────────────────────────────────────────────────────

for cmd in python3 pip; do
    command -v "$cmd" &>/dev/null || err "$cmd not found"
done

pip show build  &>/dev/null || pip install build
pip show twine  &>/dev/null || pip install twine

# ── Run tests ─────────────────────────────────────────────────────────────────

step "Running test suite..."
pip show pytest &>/dev/null || pip install pytest
python3 -m pytest tests/ -v --tb=short
ok "All tests passed"

# ── Clean previous builds ─────────────────────────────────────────────────────

step "Cleaning previous builds..."
rm -rf dist/ build/ milkyway_ctf.egg-info/
ok "Cleaned"

# ── Build ─────────────────────────────────────────────────────────────────────

step "Building wheel + source distribution..."
python3 -m build
ok "Build complete:"
ls -lh dist/

# ── Check the distribution ────────────────────────────────────────────────────

step "Checking distribution with twine..."
twine check dist/*
ok "Distribution check passed"

# ── Upload ────────────────────────────────────────────────────────────────────

if [[ $TEST_MODE -eq 1 ]]; then
    step "Uploading to TestPyPI..."
    twine upload --repository testpypi dist/*
    ok "Published to TestPyPI!"
    echo ""
    echo "  Test install:"
    echo "  pip install --index-url https://test.pypi.org/simple/ \\"
    echo "              --extra-index-url https://pypi.org/simple/ milkyway-ctf==${VERSION}"
else
    step "Uploading to PyPI..."
    twine upload dist/*
    ok "Published to PyPI!"
    echo ""
    echo "  Install with:"
    echo "  pip install milkyway-ctf==${VERSION}"
    echo "  pip install --upgrade milkyway-ctf"
fi

# ── Tag the release ───────────────────────────────────────────────────────────

if [[ $TEST_MODE -eq 0 ]]; then
    step "Creating git tag v${VERSION}..."
    if git rev-parse "v${VERSION}" &>/dev/null 2>&1; then
        warn "Tag v${VERSION} already exists — skipping"
    else
        git tag -a "v${VERSION}" -m "MilkyWay v${VERSION}"
        git push origin "v${VERSION}"
        ok "Tag v${VERSION} pushed"
    fi
fi

echo ""
ok "Done! MilkyWay v${VERSION} is live."
