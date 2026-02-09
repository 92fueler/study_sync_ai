#!/bin/bash
# Start the full StudySync AI development stack in a tmux session.
# Usage: ./scripts/startup/start-fullstack-dev.sh
#
# Layout (2 panes):
#   Left:  Backend  — Docker services + gateway  (start-backend.sh)
#   Right: Frontend — Vite dev server            (start-frontend.sh)
#
# Flags:
#   --fresh   Kill existing session and start clean (default: reattach)

set -e

cd "$(dirname "$0")/../.."
PROJECT_ROOT="$PWD"
SESSION_NAME="studysync-fullstack"
FRESH=false

# ── Parse flags ─────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --fresh) FRESH=true ;;
    esac
done

# ── Preflight ───────────────────────────────────────────────────
for cmd in tmux docker; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: $cmd is not installed."
        exit 1
    fi
done

# ── Handle existing session ─────────────────────────────────────
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    if [ "$FRESH" = true ]; then
        echo "Killing stale session '$SESSION_NAME'..."
        tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

        # Also kill leftover processes so ports are free
        lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
        pgrep -f "uvicorn.*app.main:app" 2>/dev/null | xargs kill -9 2>/dev/null || true
        lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
        sleep 1
    else
        echo "Session '$SESSION_NAME' already running."
        echo "  Attaching... (use --fresh to restart clean)"
        tmux attach-session -t "$SESSION_NAME"
        exit 0
    fi
fi

# ── Banner ──────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════╗"
echo "║  StudySync AI — Full Stack Dev           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Session  : $SESSION_NAME"
echo "  Backend  : http://localhost:8000  (docs: /docs)"
echo "  Frontend : http://localhost:3000"
echo ""
echo "  Ctrl+B D       Detach"
echo "  Ctrl+B ←/→     Switch panes"
echo "  Ctrl+B [       Scroll mode (q to exit)"
echo "  --fresh         Kill & restart clean"
echo ""

# ── Create tmux session ────────────────────────────────────────
tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50

# Left pane: Backend (Docker + Gateway)
tmux send-keys -t "$SESSION_NAME:0.0" \
    "cd '$PROJECT_ROOT' && '$PROJECT_ROOT/scripts/startup/start-backend.sh'" C-m

# Split: left | right
tmux split-window -h -t "$SESSION_NAME"

# Right pane: Frontend
tmux send-keys -t "$SESSION_NAME:0.1" \
    "cd '$PROJECT_ROOT' && '$PROJECT_ROOT/scripts/startup/start-frontend.sh'" C-m

# ── Clear scrollback in both panes so there's no stale history ──
# (The clear happens after the commands are sent so it clears any
#  shell-startup noise; the script output is what you'll see.)
for pane in 0 1; do
    tmux clear-history -t "$SESSION_NAME:0.$pane" 2>/dev/null || true
done

# Focus left (backend) pane and attach
tmux select-pane -t "$SESSION_NAME:0.0"
tmux attach-session -t "$SESSION_NAME"
