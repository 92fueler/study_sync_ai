#!/bin/bash
# Integration test script for backend-frontend interaction
# Usage: ./scripts/test/test-integration.sh

set -e

cd "$(dirname "$0")/../.."

BASE_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
TEST_USER_ID="test_user_$(date +%s)"

echo "=== StudySync AI Integration Tests ==="
echo ""

# Test 1: Backend Health
echo "1. Testing Backend Health..."
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✓ Backend is healthy"
else
    echo "   ✗ Backend health check failed"
    exit 1
fi
echo ""

# Test 2: Frontend Accessibility
echo "2. Testing Frontend Accessibility..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "   ✓ Frontend is accessible (HTTP $FRONTEND_STATUS)"
else
    echo "   ✗ Frontend not accessible (HTTP $FRONTEND_STATUS)"
    exit 1
fi
echo ""

# Test 3: CORS Headers
echo "3. Testing CORS Configuration..."
CORS_HEADERS=$(curl -s -I -H "Origin: http://localhost:3000" "$BASE_URL/health" | grep -i "access-control")
if [ -n "$CORS_HEADERS" ]; then
    echo "   ✓ CORS headers present"
else
    echo "   ⚠ CORS headers not found (may be configured differently)"
fi
echo ""

echo "=== Test Summary ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "✓ Integration tests completed!"
