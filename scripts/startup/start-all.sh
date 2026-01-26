#!/bin/bash
# Start the full StudySync AI stack with Docker Compose
# Usage: ./scripts/startup/start-all.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Starting StudySync AI ==="
echo "Loading environment from .env..."

if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    exit 1
fi

# Export env vars for docker-compose
export $(cat .env | grep -v '^#' | xargs)

echo "Building and starting containers..."
docker-compose up --build -d

echo ""
echo "=== Waiting for services to be healthy ==="
sleep 5

echo ""
echo "=== Service Status ==="
docker-compose ps

echo ""
echo "=== Health Checks ==="
echo -n "Gateway (8000): "
curl -s http://localhost:8000/health 2>/dev/null || echo "not ready"

echo -n "Redis (6379): "
docker-compose exec -T redis redis-cli ping 2>/dev/null || echo "not ready"

echo ""
echo "=== StudySync AI Started ==="
echo "Gateway API: http://localhost:8000"
echo "Swagger Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: ./scripts/startup/stop-all.sh"
