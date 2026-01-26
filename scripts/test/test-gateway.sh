#!/bin/bash
# Test Gateway API endpoints (requires gateway running)
# Usage: ./scripts/test/test-gateway.sh

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"

echo "=== Testing Gateway API ==="
echo "Gateway URL: $GATEWAY_URL"
echo ""

echo "=== Health Check ==="
curl -s "$GATEWAY_URL/health" | python -m json.tool || echo "Gateway not reachable"

echo ""
echo "=== Create Profile ==="
curl -s -X POST "$GATEWAY_URL/api/v1/profile" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user-123",
    "display_name": "Test User",
    "goals": ["Learn React", "Master TypeScript"],
    "style_dna": {
      "tone": "eli5",
      "format_pref": "outline",
      "uses_emoji": true,
      "prefers_diagrams": true
    }
  }' | python -m json.tool || echo "Profile creation failed"

echo ""
echo "=== Get Profile ==="
curl -s "$GATEWAY_URL/api/v1/profile/test-user-123" | python -m json.tool || echo "Profile get failed"

echo ""
echo "=== Get Priority Queue ==="
curl -s "$GATEWAY_URL/api/v1/queue?user_id=test-user-123" | python -m json.tool || echo "Queue get failed"

echo ""
echo "=== Gateway Test Complete ==="
