#!/bin/bash
# Test Gemini API directly with sample content
# Usage: ./scripts/test/test-gemini.sh [text]

set -e

cd "$(dirname "$0")/../.."

# Load env
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY not set!"
    exit 1
fi

TEXT="${1:-Machine learning is a subset of AI that enables systems to learn from data.}"

echo "=== Testing Gemini API ==="
echo "Input text: $TEXT"
echo ""

source .venv/bin/activate 2>/dev/null || true

python << EOF
import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("=== Topic Extraction ===")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents='''Extract the main topics from this text. Return only a JSON array of strings.
Text: $TEXT
Return ONLY the JSON array:'''
)
print(f"Topics: {response.text}")

print("\n=== Embedding Generation ===")
result = client.models.embed_content(
    model="gemini-embedding-001",
    contents="$TEXT"
)
print(f"Embedding dimensions: {len(result.embeddings[0].values)}")
print(f"First 5 values: {result.embeddings[0].values[:5]}")

print("\n=== Gemini API Test Complete ===")
EOF
