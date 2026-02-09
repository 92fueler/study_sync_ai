#!/bin/bash
# Start backend: Docker services (infra + agents + workers) then gateway locally
# Usage: ./scripts/startup/start-backend.sh
#
# This script:
#   1. Starts Redis + Postgres (waits for health check)
#   2. Builds + starts all ADK agents and RQ workers in Docker
#   3. Activates Python venv + loads .env
#   4. Runs the gateway (uvicorn) in the foreground with hot-reload

set -e

cd "$(dirname "$0")/../.."
PROJECT_ROOT="$PWD"

echo "╔══════════════════════════════════════════╗"
echo "║   StudySync AI — Backend                 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── .env check ──────────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "WARNING: .env not found. Copy .env.example to .env and fill in credentials."
fi

# ── Load environment variables ──────────────────────────────────
load_env() {
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    fi
}
load_env

# ── 1. Start infrastructure ────────────────────────────────────
echo "[1/4] Starting infrastructure (Redis, Postgres)..."
docker-compose up -d redis supabase

echo "       Waiting for Postgres to be healthy..."
RETRIES=0
MAX_RETRIES=30
until docker-compose exec -T supabase pg_isready -U postgres > /dev/null 2>&1; do
    RETRIES=$((RETRIES + 1))
    if [ $RETRIES -ge $MAX_RETRIES ]; then
        echo "ERROR: Postgres did not become ready in time."
        exit 1
    fi
    sleep 1
done
echo "       Postgres ready."

# ── 2. Build + start agents and workers ─────────────────────────
echo ""
echo "[2/4] Building and starting agents + workers..."
docker-compose up -d --build \
    ingestion-agent profile-agent planner-agent synthesis-agent orchestrator-agent \
    generation-worker notification-worker priority-worker

echo "       Waiting for agents to start..."
sleep 3

echo ""
echo "       Docker services:"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null \
    || docker-compose ps

# ── 3. Activate Python virtual environment ──────────────────────
echo ""
echo "[3/4] Setting up Python environment..."
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "       Activated .venv"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "       Activated venv"
else
    echo "       No venv found — creating .venv..."
    python3 -m venv "$PROJECT_ROOT/.venv"
    source "$PROJECT_ROOT/.venv/bin/activate"
    pip install -r "$PROJECT_ROOT/gateway/requirements.txt"
fi

# Reload env vars into the activated venv shell
load_env

# ── 4. Start gateway ───────────────────────────────────────────
echo ""
echo "[4/4] Starting gateway..."
echo ""
echo "       URL:  http://localhost:8000"
echo "       Docs: http://localhost:8000/docs"
echo ""
echo "       Press Ctrl+C to stop the gateway."
echo ""

cd "$PROJECT_ROOT/gateway"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
