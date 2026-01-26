#!/bin/bash
# Test async generation flow (requires gateway + workers)
# Usage: ./scripts/test/test-generate.sh [content_id]

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"
CONTENT_ID="${1:-content-test-123}"
USER_ID="test-user-123"

echo "=== Testing Async Generation ==="
echo "User: $USER_ID"
echo "Content: $CONTENT_ID"
echo ""

echo "=== Enqueue Generation Job ==="
RESULT=$(curl -s -X POST "$GATEWAY_URL/api/v1/generate/async" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"$USER_ID\",
    \"content_id\": \"$CONTENT_ID\",
    \"artifact_type\": \"5min\"
  }")

echo "$RESULT" | python -m json.tool || echo "Enqueue failed"

JOB_ID=$(echo "$RESULT" | python -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))" 2>/dev/null)

if [ -n "$JOB_ID" ]; then
    echo ""
    echo "=== Polling Job Status ==="
    for i in 1 2 3 4 5; do
        echo "Poll $i..."
        curl -s "$GATEWAY_URL/api/v1/generate/job/$JOB_ID" | python -m json.tool || echo "Poll failed"
        sleep 2
    done
fi

echo ""
echo "=== Generation Test Complete ==="
