#!/bin/bash
# Start RQ workers locally (requires Redis running)
# Usage: ./scripts/startup/start-workers.sh

set -e

cd "$(dirname "$0")/../.."

# Load env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "=== Starting Workers ==="
echo "Make sure Redis is running (docker-compose up -d redis)"
echo ""

# Check Redis
python -c "from workers.queue import get_redis_connection; get_redis_connection().ping()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Cannot connect to Redis at ${REDIS_URL:-redis://localhost:6379}"
    exit 1
fi

echo "Redis connected!"
echo ""
echo "Starting workers in background..."

# Start workers in background
python -m workers.generation_worker &
GENERATION_PID=$!
echo "Generation worker started (PID: $GENERATION_PID)"

python -m workers.notification_worker &
NOTIFICATION_PID=$!
echo "Notification worker started (PID: $NOTIFICATION_PID)"

python -m workers.priority_worker &
PRIORITY_PID=$!
echo "Priority worker started (PID: $PRIORITY_PID)"

echo ""
echo "Workers running. PIDs: $GENERATION_PID, $NOTIFICATION_PID, $PRIORITY_PID"
echo "To stop: kill $GENERATION_PID $NOTIFICATION_PID $PRIORITY_PID"

# Wait for all
wait
