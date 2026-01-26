#!/bin/bash
# Run integration tests (requires GEMINI_API_KEY)
# Usage: ./scripts/test/run-integration-tests.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Running Integration Tests ==="

# Load env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY not set!"
    echo "Set it in .env or export GEMINI_API_KEY=your-key"
    exit 1
fi

source .venv/bin/activate 2>/dev/null || python -m venv .venv && source .venv/bin/activate

pip install -q pytest pytest-asyncio google-genai python-dotenv

echo ""
echo "Testing with Gemini API..."
python -m pytest tests/test_integration.py -v

echo ""
echo "=== Integration Tests Complete ==="
