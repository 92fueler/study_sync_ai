#!/bin/bash
# Test worker queue operations (requires Redis)
# Usage: ./scripts/test/test-queue.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Testing Queue Operations ==="

# Load env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

source .venv/bin/activate 2>/dev/null || true

python << 'EOF'
from workers.queue import get_redis_connection, get_high_queue, get_default_queue, get_low_queue

print("=== Redis Connection ===")
conn = get_redis_connection()
print(f"PING: {conn.ping()}")

print("\n=== Queue Status ===")
high_q = get_high_queue()
default_q = get_default_queue()
low_q = get_low_queue()

print(f"High queue: {len(high_q)} jobs")
print(f"Default queue: {len(default_q)} jobs")
print(f"Low queue: {len(low_q)} jobs")

print("\n=== Test Enqueue ===")
from workers.queue import enqueue_generation

job = enqueue_generation("test-user", "test-content", "5min", high_priority=False)
print(f"Enqueued job: {job.id}")
print(f"Queue: default")
print(f"Status: {job.get_status()}")

print("\n=== Queue After Enqueue ===")
print(f"Default queue: {len(default_q)} jobs")
EOF

echo ""
echo "=== Queue Test Complete ==="
