#!/bin/bash
# Stop all StudySync AI services
# Usage: ./scripts/startup/stop-all.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Stopping StudySync AI ==="

# Stop tmux session if it exists (from start-fullstack-dev.sh)
SESSION_NAME="studysync-fullstack"
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Stopping tmux session: $SESSION_NAME"
    tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
fi

# Stop backend (uvicorn) processes
echo "Stopping backend (gateway) processes..."
# Kill by port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "  Killing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi
# Also kill by process name (uvicorn)
if pgrep -f "uvicorn.*app.main:app" > /dev/null 2>&1; then
    echo "  Killing uvicorn processes..."
    pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null || true
fi

# Stop frontend (npm dev server) processes
echo "Stopping frontend processes..."
# Kill by port 3000
if lsof -ti:3000 > /dev/null 2>&1; then
    echo "  Killing process on port 3000..."
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
fi
# Also kill vite/dev server processes (more specific to avoid killing other node processes)
if pgrep -f "vite|npm.*dev|node.*dev" > /dev/null 2>&1; then
    echo "  Killing frontend dev server processes..."
    # Be more specific - only kill if running from frontend directory
    pkill -9 -f "vite" 2>/dev/null || true
    # Kill npm run dev processes in frontend directory
    ps aux | grep -E "npm.*run.*dev|node.*vite" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
fi

# Stop Docker services (preserve volumes to keep database data)
echo "Stopping Docker services (preserving volumes to keep database data)..."
docker-compose down --remove-orphans

echo ""
echo "=== All services stopped ==="
echo "Backend (port 8000) and Frontend (port 3000) processes have been terminated."
echo "Docker containers stopped. Volumes preserved - your database data is safe!"
echo ""
echo "Note: Your materials and data are preserved in Docker volumes."
echo "To completely remove volumes (WARNING: deletes all data), use: docker-compose down -v"
