#!/bin/bash
# Run all unit tests (no external services required)
# Usage: ./scripts/test/run-unit-tests.sh

set -e

cd "$(dirname "$0")/../.."

echo "=== Running Unit Tests ==="
source .venv/bin/activate 2>/dev/null || python -m venv .venv && source .venv/bin/activate

pip install -q pytest pytest-asyncio

echo ""
python -m pytest tests/ --ignore=tests/test_integration.py -v

echo ""
echo "=== Unit Tests Complete ==="
