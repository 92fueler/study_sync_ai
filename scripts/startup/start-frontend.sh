#!/bin/bash
# Start frontend dev server (Vite + React)
# Usage: ./scripts/startup/start-frontend.sh
#
# This script:
#   1. Loads nvm and switches to the correct Node.js version
#   2. Installs/updates npm dependencies if needed
#   3. Creates .env from .env.example if missing
#   4. Runs the Vite dev server in the foreground

set -e

cd "$(dirname "$0")/../.."
PROJECT_ROOT="$PWD"

echo "╔══════════════════════════════════════════╗"
echo "║   StudySync AI — Frontend                ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── nvm helpers ─────────────────────────────────────────────────
load_nvm() {
    export NVM_DIR="$HOME/.nvm"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
        \. "$NVM_DIR/nvm.sh"
        return 0
    fi
    return 1
}

ensure_nvm_version() {
    if load_nvm; then
        if [ -f ".nvmrc" ]; then
            nvm use 2>/dev/null || true
        fi
    fi
}

# ── 1. Load nvm ────────────────────────────────────────────────
load_nvm || {
    if [ -s "$HOME/.zshrc" ] && grep -q "NVM_DIR" "$HOME/.zshrc"; then
        load_nvm
    elif [ -s "$HOME/.bashrc" ] && grep -q "NVM_DIR" "$HOME/.bashrc"; then
        load_nvm
    fi
}

# ── 2. Check / switch Node version ─────────────────────────────
NODE_VERSION=$(node --version 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1 || echo "")
REQUIRED_VERSION="24"

if [ -z "$NODE_VERSION" ] || [ "$NODE_VERSION" != "$REQUIRED_VERSION" ]; then
    echo "[node] Version mismatch (need v${REQUIRED_VERSION}.x, have v${NODE_VERSION:-none})"

    if load_nvm && type nvm &>/dev/null 2>&1; then
        cd "$PROJECT_ROOT/frontend"
        if [ -f .nvmrc ]; then
            echo "[node] Switching to version from .nvmrc..."
            set +e
            nvm use &>/dev/null 2>&1
            NVM_EXIT=$?
            set -e
            if [ $NVM_EXIT -ne 0 ]; then
                echo "[node] Installing from .nvmrc..."
                nvm install
                nvm use
            fi
        else
            echo "[node] Installing v${REQUIRED_VERSION}..."
            set +e; nvm use $REQUIRED_VERSION &>/dev/null 2>&1; NVM_EXIT=$?; set -e
            if [ $NVM_EXIT -ne 0 ]; then
                nvm install $REQUIRED_VERSION
                nvm use $REQUIRED_VERSION
            fi
        fi
        cd "$PROJECT_ROOT"
    else
        echo "ERROR: nvm is not available. Install nvm or Node.js v${REQUIRED_VERSION} manually."
        exit 1
    fi
fi

echo "[node] Using $(node --version)"

# ── 3. Install dependencies ────────────────────────────────────
cd "$PROJECT_ROOT/frontend"
ensure_nvm_version .

if [ ! -d "node_modules" ]; then
    echo "[npm]  Installing dependencies..."
    npm install
elif [ "package.json" -nt "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
    echo "[npm]  Updating dependencies..."
    npm install
fi

# ── 4. Create .env if missing ──────────────────────────────────
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[env]  Created .env from .env.example"
fi

# ── 5. Start dev server ────────────────────────────────────────
echo ""
echo "       URL: http://localhost:3000"
echo ""
echo "       Press Ctrl+C to stop."
echo ""

ensure_nvm_version .
exec npm run dev
