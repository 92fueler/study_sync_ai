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

log "--- Priority Queue (can take up to 90s) ---"
curl --max-time 90 -sS "$GATEWAY_URL/api/v1/queue?user_id=$USER_ID" | $PYTHON_CMD -m json.tool

log "--- Async Generate (5min) ---"
GEN_RESULT=$(curl -sS -X POST "$GATEWAY_URL/api/v1/generate/async" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\": \"$USER_ID\", \"content_id\": \"$CONTENT_ID\", \"artifact_type\": \"5min\"}")

echo "$GEN_RESULT" | $PYTHON_CMD -m json.tool
JOB_ID=$(echo "$GEN_RESULT" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('job_id',''))")

if [ -z "$JOB_ID" ]; then
  echo "ERROR: job_id not returned"
  exit 1
fi

log "--- Poll Job Status ---"
MAX_POLLS=20
for i in $(seq 1 $MAX_POLLS); do
  STATUS_JSON=$(curl -sS "$GATEWAY_URL/api/v1/generate/job/$JOB_ID")
  echo "$STATUS_JSON" | $PYTHON_CMD -m json.tool
  STATUS=$(echo "$STATUS_JSON" | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin).get('status',''))")
  if [ "$STATUS" = "finished" ]; then
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

log "--- Notifications ---"
curl -sS "$GATEWAY_URL/api/v1/notifications?user_id=$USER_ID" | $PYTHON_CMD -m json.tool

log "=== E2E Smoke Test Complete ==="
