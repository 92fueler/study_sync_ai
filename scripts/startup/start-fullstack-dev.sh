#!/bin/bash
# Start both backend and frontend in development mode using tmux
# Usage: ./scripts/startup/start-fullstack-dev.sh

set -e

cd "$(dirname "$0")/../.."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "ERROR: tmux is not installed"
    echo "Install tmux or run start-backend.sh and start-frontend.sh in separate terminals"
    exit 1
fi

SESSION_NAME="studysync-fullstack"

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Session $SESSION_NAME already exists"
    echo "Attaching to existing session..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

echo "=== Starting Full Stack Development Environment ==="
echo "Creating tmux session: $SESSION_NAME"
echo ""
echo "Note: Docker containers will be rebuilt to pick up code changes"
echo ""
echo "Commands:"
echo "  Ctrl+B then D  - Detach from session"
echo "  Ctrl+B then X  - Kill current pane"
echo "  Ctrl+B then C  - Create new pane"
echo "  tmux attach -t $SESSION_NAME  - Reattach to session"
echo ""

# Create new tmux session
tmux new-session -d -s "$SESSION_NAME" -x 200 -y 50

# Split window horizontally
tmux split-window -h -t "$SESSION_NAME"

# Start backend in left pane (script handles infrastructure, venv, etc.)
tmux send-keys -t "$SESSION_NAME:0.0" "cd '$PWD' && ./scripts/startup/start-backend.sh" C-m

# Start frontend in right pane (script handles nvm, node_modules, etc.)
tmux send-keys -t "$SESSION_NAME:0.1" "cd '$PWD' && ./scripts/startup/start-frontend.sh" C-m

# Select first pane and attach
tmux select-pane -t "$SESSION_NAME:0.0"
tmux attach-session -t "$SESSION_NAME"
