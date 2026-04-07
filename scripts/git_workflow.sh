#!/usr/bin/env bash
# scripts/git_workflow.sh
# ─────────────────────────────────────────────────────────────────────────────
# Interactive helper for MilkyWay's git branch → test → merge workflow.
# Run from the project root.
#
# Usage:
#   bash scripts/git_workflow.sh new      → create a test/feat branch
#   bash scripts/git_workflow.sh test     → run tests on current branch
#   bash scripts/git_workflow.sh merge    → merge current branch into main
#   bash scripts/git_workflow.sh release  → tag + trigger PyPI publish

set -euo pipefail

CMD="${1:-help}"
CYAN="\033[0;36m"; GREEN="\033[0;32m"
YELLOW="\033[0;33m"; RED="\033[0;31m"
BOLD="\033[1m"; RESET="\033[0m"

banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
  __  __ _ _ _          __        __
 |  \/  (_) | | ___   __\ \      / /_ _ _   _
 | |\/| | | | |/ / | | \ \ /\ / / _` | | | |
 | |  | | | |   <| |_| |\ V  V / (_| | |_| |
 |_|  |_|_|_|_|\_\__, | \_/\_/ \__,_|\__, |
                  |___/               |___/
  Git Workflow Helper
EOF
    echo -e "${RESET}"
}

step()    { echo -e "\n${CYAN}${BOLD}[*] $*${RESET}"; }
ok()      { echo -e "${GREEN}[+] $*${RESET}"; }
warn()    { echo -e "${YELLOW}[!] $*${RESET}"; }
err()     { echo -e "${RED}[✗] $*${RESET}"; exit 1; }
ask()     { echo -e -n "${YELLOW}[?] $* ${RESET}"; read -r REPLY; echo "$REPLY"; }

current_branch() { git rev-parse --abbrev-ref HEAD; }
is_clean()       { git diff --quiet && git diff --cached --quiet; }

# ── new ───────────────────────────────────────────────────────────────────────
cmd_new() {
    banner

    echo "Branch types:"
    echo "  1) test/vX.Y.Z   — release candidate / integration test"
    echo "  2) feat/<name>   — new feature"
    echo "  3) fix/<name>    — bug fix"
    echo "  4) docs/<name>   — documentation"
    echo ""
    TYPE=$(ask "Choose type (1-4):")
    NAME=$(ask "Branch name (e.g. v1.2.1 or uranus-improvements):")

    case $TYPE in
        1) BRANCH="test/$NAME" ;;
        2) BRANCH="feat/$NAME" ;;
        3) BRANCH="fix/$NAME"  ;;
        4) BRANCH="docs/$NAME" ;;
        *) err "Invalid choice" ;;
    esac

    step "Syncing main branch..."
    git checkout main
    git pull origin main

    step "Creating branch $BRANCH..."
    git checkout -b "$BRANCH"
    ok "You are now on branch: $BRANCH"

    echo ""
    echo "  Next steps:"
    echo "  1. Make your changes"
    echo "  2. git add -p && git commit -m 'feat: describe change'"
    echo "  3. bash scripts/git_workflow.sh test"
    echo "  4. bash scripts/git_workflow.sh merge"
}

# ── test ──────────────────────────────────────────────────────────────────────
cmd_test() {
    BRANCH=$(current_branch)
    step "Running tests on branch: $BRANCH"

    # Check venv
    if [[ -z "${VIRTUAL_ENV:-}" ]]; then
        warn "No virtual environment active."
        warn "Activate with: source .venv/bin/activate"
        warn "Or create one: python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'"
    fi

    step "Running pytest..."
    python3 -m pytest tests/ -v --tb=short
    ok "All tests passed on $BRANCH"

    step "Smoke-testing CLI imports..."
    python3 -c "
from milkyway.cli.main import cli
from milkyway.core.db import SaturnDB
from milkyway.shell import PLANETS
print(f'  CLI: OK')
print(f'  DB: OK')
print(f'  Planets: {len(PLANETS)} loaded')
"
    ok "CLI smoke test passed"

    step "Checking milkyway --version..."
    python3 -m milkyway.cli.main --version 2>/dev/null || \
        python3 -c "from milkyway import __version__; print(f'MilkyWay {__version__}')"

    echo ""
    ok "All checks passed on branch: $BRANCH"
    echo "  Ready to merge? Run: bash scripts/git_workflow.sh merge"
}

# ── merge ─────────────────────────────────────────────────────────────────────
cmd_merge() {
    BRANCH=$(current_branch)
    [[ "$BRANCH" == "main" ]] && err "Already on main — checkout your feature branch first"

    banner
    step "Merging $BRANCH → main"

    # Run tests first
    step "Running tests before merge..."
    python3 -m pytest tests/ -v --tb=short || err "Tests failed — fix before merging"
    ok "Tests passed"

    # Check for uncommitted changes
    if ! is_clean; then
        warn "Uncommitted changes detected"
        git status --short
        CONTINUE=$(ask "Commit them now? (y/N):")
        if [[ "${CONTINUE,,}" == "y" ]]; then
            MSG=$(ask "Commit message:")
            git add .
            git commit -m "$MSG"
        else
            err "Commit or stash changes before merging"
        fi
    fi

    # Push branch
    step "Pushing $BRANCH to GitHub..."
    git push -u origin "$BRANCH"
    ok "Branch pushed"

    # Switch to main and merge
    step "Switching to main and pulling latest..."
    git checkout main
    git pull origin main

    step "Merging $BRANCH into main..."
    git merge "$BRANCH" --no-ff -m "merge: $BRANCH → main"
    ok "Merge complete"

    step "Pushing main to GitHub..."
    git push origin main
    ok "main pushed"

    # Delete the branch
    CLEANUP=$(ask "Delete branch $BRANCH? (Y/n):")
    if [[ "${CLEANUP,,}" != "n" ]]; then
        git branch -d "$BRANCH"
        git push origin --delete "$BRANCH" 2>/dev/null || true
        ok "Branch $BRANCH deleted"
    fi

    echo ""
    ok "Done! $BRANCH merged into main"
    echo "  Next: bash scripts/git_workflow.sh release"
}

# ── release ───────────────────────────────────────────────────────────────────
cmd_release() {
    BRANCH=$(current_branch)
    [[ "$BRANCH" != "main" ]] && err "Must be on main to release. Run: git checkout main"

    VERSION=$(python3 -c "
import re
text = open('pyproject.toml').read()
m = re.search(r'version\s*=\s*\"([^\"]+)\"', text)
print(m.group(1))
")

    banner
    step "Releasing MilkyWay v${VERSION}"
    warn "This will tag v${VERSION} and push it — triggering GitHub Actions to publish to PyPI"
    CONFIRM=$(ask "Confirm release v${VERSION}? (yes/N):")
    [[ "${CONFIRM,,}" != "yes" ]] && err "Cancelled"

    # Check tag doesn't exist
    if git rev-parse "v${VERSION}" &>/dev/null 2>&1; then
        err "Tag v${VERSION} already exists"
    fi

    step "Creating and pushing tag v${VERSION}..."
    git tag -a "v${VERSION}" -m "MilkyWay v${VERSION} — The Galactic CTF Orchestrator"
    git push origin "v${VERSION}"
    ok "Tag v${VERSION} pushed"

    echo ""
    ok "GitHub Actions will now:"
    echo "  1. Run tests on Python 3.9/3.10/3.11/3.12"
    echo "  2. Build wheel + source distribution"
    echo "  3. Publish to PyPI automatically"
    echo "  4. Create GitHub Release with download links"
    echo ""
    echo "  Track progress: https://github.com/kazim-45/milkyway/actions"
    echo ""
    echo "  After ~5 minutes:"
    echo "  pip install milkyway-ctf==${VERSION}"
}

# ── help ──────────────────────────────────────────────────────────────────────
cmd_help() {
    banner
    echo "  Usage: bash scripts/git_workflow.sh <command>"
    echo ""
    echo "  Commands:"
    echo "    new      Create a new test/feat/fix/docs branch"
    echo "    test     Run tests + smoke check on current branch"
    echo "    merge    Merge current branch into main (tests run first)"
    echo "    release  Tag current version and push (triggers PyPI publish)"
    echo ""
    echo "  Full workflow:"
    echo "    bash scripts/git_workflow.sh new        # 1. create branch"
    echo "    # ... make changes ..."
    echo "    bash scripts/git_workflow.sh test       # 2. verify"
    echo "    bash scripts/git_workflow.sh merge      # 3. merge to main"
    echo "    bash scripts/git_workflow.sh release    # 4. publish to PyPI"
}

# ── Dispatch ──────────────────────────────────────────────────────────────────
case $CMD in
    new)     cmd_new     ;;
    test)    cmd_test    ;;
    merge)   cmd_merge   ;;
    release) cmd_release ;;
    *)       cmd_help    ;;
esac
