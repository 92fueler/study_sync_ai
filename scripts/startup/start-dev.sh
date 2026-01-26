#!/bin/bash
# Start only infrastructure (Redis, Postgres) for local development
# Run agents/gateway manually for debugging
# Usage: ./scripts/startup/start-dev.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Starting Dev Infrastructure ==="

# Start only Redis and Postgres
docker-compose up -d redis supabase

echo "Waiting for services..."
sleep 3

echo ""
echo "=== Infrastructure Status ==="
docker-compose ps redis supabase

echo ""
echo "=== Connection Info ==="
echo "Redis: redis://localhost:6379"
echo "Postgres: postgresql://postgres:postgres@localhost:5432/studysync"
echo ""
echo "To run gateway locally:"
echo "  source .venv/bin/activate"
echo "  cd gateway && GEMINI_API_KEY=\$GEMINI_API_KEY python -m uvicorn app.main:app --port 8000 --reload"
echo ""
echo "To run workers locally:"
echo "  python -m workers.generation_worker"
