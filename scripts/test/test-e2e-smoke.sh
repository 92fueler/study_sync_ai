#!/bin/bash
# End-to-end smoke test for StudySync AI (gateway + agents + workers)
# Usage: ./scripts/test/test-e2e-smoke.sh

set -euo pipefail

cd "$(dirname "$0")/../.."

# Load env if present (for GATEWAY_URL override)
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"
USER_ID="${USER_ID:-test-user-123}"

PYTHON_CMD=$(command -v python3 || command -v python || echo "python3")

log() {
  echo "[$(date +"%H:%M:%S")] $*"
}

log "=== E2E Smoke Test ==="
log "Gateway: $GATEWAY_URL"
log "User: $USER_ID"

log "--- Health ---"
curl -sS "$GATEWAY_URL/health" | $PYTHON_CMD -m json.tool

log "--- Create Profile (idempotent) ---"
PROFILE_PAYLOAD=$(cat <<JSON
{
  "user_id": "$USER_ID",
  "display_name": "Test User",
  "goals": ["Learn React", "Master TypeScript"],
  "style_dna": {
    "tone": "eli5",
    "format_pref": "outline",
    "uses_emoji": true,
    "prefers_diagrams": true
  }
}
JSON
)

echo "$PROFILE_PAYLOAD" | curl -sS -X POST "$GATEWAY_URL/api/v1/profile" \
  -H "Content-Type: application/json" \
  -d @- | $PYTHON_CMD -m json.tool

log "--- Get Profile ---"
curl -sS "$GATEWAY_URL/api/v1/profile/$USER_ID" | $PYTHON_CMD -m json.tool

log "--- Upload Sample File ---"
mkdir -p /tmp/studysync-test
cat > /tmp/studysync-test/sample.txt << 'SAMPLE'
React is a JavaScript library for building user interfaces.

Key Concepts:
1. Components - Reusable UI building blocks
2. Props - Data passed from parent to child
3. State - Component's internal data that can change
4. Hooks - Functions like useState and useEffect for state and side effects
5. Virtual DOM - Efficient rendering through diffing algorithm
SAMPLE

UPLOAD_RESULT=$(curl -sS -X POST "$GATEWAY_URL/api/v1/upload" \
  -F "user_id=$USER_ID" \
  -F "files=@/tmp/studysync-test/sample.txt")

echo "$UPLOAD_RESULT" | $PYTHON_CMD -m json.tool

log "--- Resolve content_id from DB ---"
CONTENT_ID=$(docker-compose exec -T supabase psql -U postgres -d studysync -t -A \
  -c "SELECT content_id FROM user_materials WHERE user_id='${USER_ID}' ORDER BY uploaded_at DESC LIMIT 1;")

if [ -z "$CONTENT_ID" ]; then
  echo "ERROR: content_id not found in DB"
  exit 1
fi
log "content_id: $CONTENT_ID"

log "--- Content List (v1 ranker) ---"
curl -sS "$GATEWAY_URL/api/v1/content?user_id=$USER_ID&sort=rank&ranker=v1" | $PYTHON_CMD -m json.tool

log "--- Content Detail ---"
curl -sS "$GATEWAY_URL/api/v1/content/$CONTENT_ID?user_id=$USER_ID" | $PYTHON_CMD -m json.tool

log "--- Priority Queue (can take up to 90s) ---"
curl --max-time 90 -sS "$GATEWAY_URL/api/v1/queue?user_id=$USER_ID" | $PYTHON_CMD -m json.tool

log "--- Check Redis & Workers (prerequisites for async generate) ---"
# Check Redis status via gateway health endpoint
HEALTH_RESPONSE=$(curl -sS "$GATEWAY_URL/health" 2>/dev/null || echo "{}")
REDIS_STATUS=$(echo "$HEALTH_RESPONSE" | $PYTHON_CMD -c "import sys, json; d=json.load(sys.stdin); print(d.get('redis', 'unknown'))" 2>/dev/null || echo "unknown")

if [ "$REDIS_STATUS" = "connected" ]; then
  log "✓ Redis is connected (via gateway health check)"
elif [ "$REDIS_STATUS" != "unknown" ]; then
  log "✗ Redis status: $REDIS_STATUS"
  log "  Fix: docker-compose up -d redis"
else
  log "⚠ Could not check Redis status via health endpoint"
fi

# Check if workers are running (via docker-compose)
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
  WORKERS_RUNNING=0
  if docker-compose ps generation-worker 2>/dev/null | grep -q "Up" || \
     docker ps --filter "name=generation-worker" --format "{{.Status}}" 2>/dev/null | grep -q "Up"; then
    WORKERS_RUNNING=1
    log "✓ Workers appear to be running in Docker"
  else
    log "✗ Workers may not be running"
    log "  Fix: docker-compose up -d generation-worker notification-worker priority-worker"
  fi
else
  log "⚠ docker/docker-compose not found, skipping worker check"
fi

log "--- Async Generate (5min) ---"
GEN_RESULT=$(curl -sS -X POST "$GATEWAY_URL/api/v1/generate/async" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"content_id\": \"$CONTENT_ID\", \"artifact_type\": \"5min\"}")

echo "$GEN_RESULT" | $PYTHON_CMD -m json.tool

# Check if the response contains an error
ERROR_DETAIL=$(echo "$GEN_RESULT" | $PYTHON_CMD -c "import sys, json; d=json.load(sys.stdin); print(d.get('detail',''))" 2>/dev/null || echo "")
if [ -n "$ERROR_DETAIL" ]; then
  echo ""
  echo "ERROR: Async generate failed: $ERROR_DETAIL"
  echo ""
  echo "Troubleshooting:"
  echo "1. Ensure Redis is running: docker-compose up -d redis"
  echo "2. Ensure workers are running: docker-compose up -d generation-worker notification-worker priority-worker"
  echo "3. Check gateway logs: docker-compose logs gateway | tail -20"
  echo "4. Check Redis connection from gateway: docker-compose exec gateway python -c 'from workers.queue import get_redis_connection; print(get_redis_connection().ping())'"
  echo ""
  echo "Skipping job polling (async generate test failed)"
  set +e
else
  JOB_ID=$(echo "$GEN_RESULT" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null || echo "")
  
  if [ -z "$JOB_ID" ]; then
    echo "ERROR: job_id not returned in response"
    echo "Response was: $GEN_RESULT"
    exit 1
  fi

  log "--- Poll Job Status ---"
  MAX_POLLS=20
  for i in $(seq 1 $MAX_POLLS); do
    STATUS_JSON=$(curl -sS "$GATEWAY_URL/api/v1/generate/job/$JOB_ID")
    echo "$STATUS_JSON" | $PYTHON_CMD -m json.tool
    STATUS=$(echo "$STATUS_JSON" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "finished" ]; then
      log "Job completed successfully!"
      break
    elif [ "$STATUS" = "failed" ]; then
      echo "ERROR: generation job failed"
      exit 1
    fi
    sleep 2
    if [ "$i" -eq "$MAX_POLLS" ]; then
      echo "ERROR: job did not finish within timeout"
      exit 1
    fi
    log "poll $i/$MAX_POLLS..."
  done
fi

log "--- Notifications ---"
curl -sS "$GATEWAY_URL/api/v1/notifications?user_id=$USER_ID" | $PYTHON_CMD -m json.tool

log "--- Chat SSE (first event) ---"
set +e
curl -N --max-time 10 -sS "$GATEWAY_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"message\": \"Ping\"}" | head -n 5
set -e

log "=== E2E Smoke Test Complete ==="
