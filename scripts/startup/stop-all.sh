#!/bin/bash
# Stop all StudySync AI services (local processes + Docker containers)
# Usage: ./scripts/startup/stop-all.sh
#
# Stops:
#   1. tmux session (kills all panes, clears history)
#   2. Docker containers (frees port 8000 if gateway ran in Docker)
#   3. Gateway (uvicorn on port 8000)
#   4. Frontend (vite/node on port 3000)
#
# Database volumes are preserved by default.

cd "$(dirname "$0")/../.."

# Docker Compose: prefer "docker compose" (v2) then "docker-compose" (v1)
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    DC="docker compose"
elif command -v docker-compose &> /dev/null; then
    DC="docker-compose"
else
    DC=""
fi

echo "╔══════════════════════════════════════════╗"
echo "║  StudySync AI — Stop All                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Kill tmux session ───────────────────────────────────────
SESSION_NAME="studysync-fullstack"
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "[tmux]     Killing session '$SESSION_NAME'..."
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
    echo "           Done."
else
    echo "[tmux]     No active session."
fi

# ── 2. Stop Docker containers first (frees port 8000 if gateway ran in Docker) ─
echo ""
echo "[docker]   Stopping containers (preserving volumes)..."
if [ -n "$DC" ]; then
    if $DC ps -q 2>/dev/null | grep -q .; then
        $DC down --remove-orphans 2>/dev/null
        echo "           All containers stopped."
    else
        echo "           No running containers."
    fi
else
    echo "           Docker Compose not found, skipping."
fi

# ── 3. Stop Gateway (port 8000) ────────────────────────────────
echo ""
echo "[gateway]  Stopping port 8000..."
PIDS=$(lsof -ti:8000 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "$PIDS" | xargs kill 2>/dev/null || true
    sleep 2
    PIDS=$(lsof -ti:8000 2>/dev/null || true)
    [ -n "$PIDS" ] && echo "$PIDS" | xargs kill -9 2>/dev/null || true
    echo "           Stopped."
else
    echo "           Not running."
fi
# Orphan uvicorn processes
pgrep -f "uvicorn.*app.main:app" 2>/dev/null | xargs kill -9 2>/dev/null || true

# ── 4. Stop Frontend (port 3000) ───────────────────────────────
echo ""
echo "[frontend] Stopping port 3000..."
PIDS=$(lsof -ti:3000 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo "$PIDS" | xargs kill 2>/dev/null || true
    sleep 1
    PIDS=$(lsof -ti:3000 2>/dev/null || true)
    [ -n "$PIDS" ] && echo "$PIDS" | xargs kill -9 2>/dev/null || true
    echo "           Stopped."
else
    echo "           Not running."
fi

# ── Summary ────────────────────────────────────────────────────
echo ""
echo "=== All services stopped ==="
echo ""
echo "  Volumes preserved. To wipe data:  docker-compose down -v"
echo "  To restart:  ./scripts/startup/start-fullstack-dev.sh"
echo "  Fresh start: ./scripts/startup/start-fullstack-dev.sh --fresh"
