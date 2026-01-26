#!/bin/bash
# Stop all StudySync AI services
# Usage: ./scripts/startup/stop-all.sh

cd "$(dirname "$0")/../.."

echo "=== Stopping StudySync AI ==="
docker-compose down

echo "=== All services stopped ==="
