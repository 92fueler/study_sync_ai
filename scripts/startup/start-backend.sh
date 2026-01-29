#!/bin/bash
# Start backend (gateway) service
# Usage: ./scripts/startup/start-backend.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Starting Backend (Gateway) ==="

# Check if .env exists
if [ ! -f .env ]; then
    echo "WARNING: .env file not found!"
    echo "Copy .env.example to .env and fill in your credentials"
fi

# Start infrastructure if not running
if ! docker-compose ps redis supabase | grep -q "Up"; then
    echo "Starting infrastructure (Redis, Postgres)..."
    docker-compose up -d redis supabase
    echo "Waiting for infrastructure..."
    sleep 3
fi

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "WARNING: No virtual environment found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -r gateway/requirements.txt
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo ""
echo "Starting gateway on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd gateway
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
