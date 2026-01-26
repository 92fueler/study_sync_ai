#!/bin/bash
# Test file upload flow (requires gateway running)
# Usage: ./scripts/test/test-upload.sh [file_path]

set -e

cd "$(dirname "$0")/../.."

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8000}"
FILE_PATH="${1:-}"

echo "=== Testing Upload Flow ==="

# Create sample file if none provided
if [ -z "$FILE_PATH" ]; then
    echo "No file provided, creating sample..."
    mkdir -p /tmp/studysync-test
    cat > /tmp/studysync-test/sample.txt << 'SAMPLE'
React is a JavaScript library for building user interfaces.

Key Concepts:
1. Components - Reusable UI building blocks
2. Props - Data passed from parent to child
3. State - Component's internal data that can change
4. Hooks - Functions like useState and useEffect for state and side effects
5. Virtual DOM - Efficient rendering through diffing algorithm

React makes it painless to create interactive UIs. Design simple views for each state in your application, and React will efficiently update and render just the right components when your data changes.
SAMPLE
    FILE_PATH="/tmp/studysync-test/sample.txt"
    echo "Created: $FILE_PATH"
fi

echo ""
echo "=== Uploading: $FILE_PATH ==="
curl -s -X POST "$GATEWAY_URL/api/v1/upload" \
  -F "user_id=test-user-123" \
  -F "files=@$FILE_PATH" | python -m json.tool || echo "Upload failed"

echo ""
echo "=== Upload Test Complete ==="
