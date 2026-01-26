# Implementation: Verification Plan

> **Document**: impl-05-verification.md  
> **Purpose**: Health checks, integration tests, end-to-end validation

---

## 1. Infrastructure Health Checks

### 1.1 Service Startup

After `docker-compose up`, verify all services are running:

```bash
# Check all containers are up
docker-compose ps

# Expected: All services show "Up" status
# frontend, gateway, ingestion-agent, profile-agent, 
# synthesis-agent, planner-agent, orchestrator-agent, 
# redis, worker, supabase
```

### 1.2 Individual Service Health

```bash
# Gateway
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# ADK Agents (may return 404 for /health; this is expected)
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health

# Redis
docker-compose exec redis redis-cli ping
# Expected: PONG

# Supabase
docker-compose exec supabase pg_isready
# Expected: accepting connections
```

### 1.3 ADK Session & Run Smoke Test

```bash
# Create session
curl -X POST "http://localhost:8001/apps/ingestion/users/test-user/sessions" \
  -H "Content-Type: application/json" \
  -d '{"id":"test-session-123"}' | jq .

# Run agent
curl -X POST "http://localhost:8001/run_sse" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "ingestion",
    "user_id": "test-user",
    "session_id": "test-session-123",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Ping"}]
    }
  }' | jq .
```

---

## 2. ADK Runtime Communication Tests

### 2.1 Basic Run via Gateway

```bash
# Call upload endpoint and verify it triggers ADK /run_sse for ingestion
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=test-user" \
  -F "files=@test.txt"
# Expected: 200 OK with task_id and content_id in response
```

### 2.2 Inter-Agent Orchestration

Not implemented yet (no dedicated chain-test endpoint).

---

## 3. Database Tests

### 3.1 Schema Verification

```bash
# Connect to database
docker-compose exec supabase psql -U postgres -d studysync

# List tables
\dt

# Expected tables:
# content_items, user_materials, user_profiles, artifacts,
# feedback, background_jobs, behavior_signals, notifications
```

### 3.2 CRUD Operations

```bash
# Create test profile
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "display_name": "Test User",
    "goals": ["Learn React", "Master TypeScript"],
    "style_dna": {
      "tone": "eli5",
      "format_pref": "outline",
      "uses_emoji": true,
      "prefers_diagrams": true
    }
  }'
# Expected: 201 Created with profile data

# Retrieve profile
curl http://localhost:8000/api/v1/profile/test-user
# Expected: Returns the profile we just created

# Update profile
curl -X PUT http://localhost:8000/api/v1/profile/test-user \
  -H "Content-Type: application/json" \
  -d '{"goals": ["Learn Rust"]}'
# Expected: 200 OK, profile_version incremented
```

---

## 4. Upload Flow Test

### 4.1 File Upload

```bash
# Create a test PDF (or use any PDF file)
echo "Test content for PDF" > test.txt

# Upload file
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=test-user" \
  -F "files=@test.txt"
# Expected: 200 OK with content_id

# Verify in database
docker-compose exec supabase psql -U postgres -d studysync \
  -c "SELECT id, user_id, status FROM user_materials WHERE user_id = 'test-user' ORDER BY uploaded_at DESC LIMIT 5;"
```

### 4.2 Ingestion Processing

```bash
# Check material status changes
# Poll until status = 'PROCESSED'
curl http://localhost:8000/api/v1/materials?user_id=test-user | jq '.[0].status'
# Expected: "PROCESSED" (may take a few seconds)

# Verify embedding was generated
docker-compose exec supabase psql -U postgres -d studysync \
  -c "SELECT id, title, embedding IS NOT NULL as has_embedding FROM content_items LIMIT 5;"
# Expected: has_embedding = true
```

---

## 5. Generation Flow Test

### 5.1 Artifact Generation

```bash
# Generate artifact for user (requires content_ids until planner parsing is wired)
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "content_ids": ["<content-id>"],
    "time_available_minutes": 25
  }'
# Expected: Returns artifact with:
# - id
# - artifact_content (markdown)
# - artifact_5min (5-minute version)
# - estimated_minutes
# - priority_score
# - priority_reasoning
```

### 5.2 Verify Artifact Storage

```bash
# Retrieve artifact by ID
curl http://localhost:8000/api/v1/artifacts/{artifact_id}
# Expected: Artifact payload (via Synthesis agent)

# Check database (if synthesis tools stored artifacts)
docker-compose exec supabase psql -U postgres -d studysync \
  -c "SELECT id, artifact_type, estimated_minutes FROM artifacts WHERE user_id = 'test-user';"
# Expected: Shows generated artifacts
```

### 5.3 Priority Queue

```bash
# Get prioritized queue (can take 20-60s due to LLM calls)
curl --max-time 90 http://localhost:8000/api/v1/queue?user_id=test-user
# Expected: Response payload from Planner agent (wrapper includes "response")
```

---

## 6. Background Generation Test

Background jobs are scheduled via the Orchestrator agent tools (ADK `/run_sse`), not HTTP endpoints.

```bash
# Example: schedule a 5-min job via ADK /run_sse
curl -X POST "http://localhost:8005/run_sse" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "orchestrator",
    "user_id": "test-user",
    "session_id": "job-session-1",
    "new_message": {
      "role": "user",
      "parts": [{"text": "Schedule generate_5min_new for content_id: some-content-id"}]
    }
  }'
```

---

## 7. Notification Test

```bash
# Complete a generation
# ... (run generation flow)

# Check for notification created
curl http://localhost:8000/api/v1/notifications?user_id=test-user
# Expected: Wrapper with "response" from Orchestrator agent

# Check badge count
curl http://localhost:8000/api/v1/notifications/badge?user_id=test-user
# Expected: Wrapper with "response" from Orchestrator agent
```

---

## 8. Frontend Smoke Test

### 8.1 Manual UI Test

1. Open `http://localhost:3000`
2. Navigate to Upload page
3. Drag and drop a PDF file
4. Verify file appears in list
5. Click "Generate"
6. Verify loading state shown
7. Verify artifact renders with markdown
8. Verify Mermaid diagrams render (if any)
9. Check priority queue page shows ranking

### 8.2 PWA Test (if implemented)

1. Open DevTools → Application → Service Workers
2. Verify service worker is registered
3. Go offline (DevTools → Network → Offline)
4. Verify 5-min summaries still accessible
5. Verify offline indicator shown

---

## 9. End-to-End Demo Flow

Run this complete flow to verify demo readiness:

```bash
# 1. Create user profile
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "goals": ["Learn System Design", "Master Distributed Systems"],
    "style_dna": {"tone": "eli5", "prefers_diagrams": true}
  }'

# 2. Upload 3 documents
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=demo-user" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@doc3.pdf"

# 3. Wait for processing (poll or sleep)
sleep 10

# 4. Check priority queue
curl http://localhost:8000/api/v1/queue?user_id=demo-user | jq '.[0]'
# Should show top priority with reasoning

# 5. Generate time-aware artifact
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user", "time_available_minutes": 20}'

# 6. Verify 5-min version also created
curl http://localhost:8000/api/v1/artifacts?user_id=demo-user&type=5min

# 7. Change style and regenerate
curl -X PUT http://localhost:8000/api/v1/profile/demo-user \
  -H "Content-Type: application/json" \
  -d '{"style_dna": {"tone": "academic"}}'

curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user"}'

# Compare: should be noticeably different tone
```

---

## 10. Test Data

### Sample Test Profile

```json
{
  "user_id": "test-user",
  "display_name": "Test User",
  "goals": ["Learn React", "Master TypeScript", "Understand System Design"],
  "style_dna": {
    "tone": "eli5",
    "format_pref": "outline",
    "uses_emoji": true,
    "prefers_diagrams": true
  },
  "calendar_context": {
    "commute_times": ["08:00-08:30", "18:00-18:30"],
    "work_hours": "09:00-17:00",
    "timezone": "America/Los_Angeles"
  }
}
```

### Sample Test Content

Create test files with varied content:
- `react-basics.txt` - React fundamentals
- `typescript-advanced.txt` - TypeScript advanced types
- `system-design.pdf` - System design principles

This allows testing:
- Priority ranking (which aligns with goals)
- Clustering (React + TypeScript might cluster)
- Different file types

---

## 11. Automated Test Suite

### 11.1 Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# For integration tests, set GEMINI_API_KEY
export GEMINI_API_KEY=your-api-key
# Or create .env file in project root:
echo "GEMINI_API_KEY=your-api-key" > .env
```

### 11.2 Running Unit Tests

Unit tests mock all external dependencies (Gemini API, database) and run without network access.

```bash
# Run all unit tests (53 tests)
pytest tests/ --ignore=tests/test_integration.py -v

# Run specific agent tests
pytest tests/test_ingestion_agent.py -v
pytest tests/test_synthesis_agent.py -v
pytest tests/test_planner_agent.py -v
pytest tests/test_profile_agent.py -v
pytest tests/test_orchestrator_agent.py -v

# Run with coverage
pytest tests/ --ignore=tests/test_integration.py --cov=agents --cov-report=term-missing
```

### 11.3 Running Integration Tests

Integration tests call the real Gemini API. Requires `GEMINI_API_KEY` environment variable.

```bash
# Run all integration tests (7 tests)
GEMINI_API_KEY=your-key pytest tests/test_integration.py -v

# Tests included:
# - test_extract_topics_real_api: Topic extraction with Gemini
# - test_generate_embedding_real_api: Embedding generation (3072 dimensions)
# - test_build_system_instruction: Style DNA → system prompt
# - test_calc_trending: Recency scoring algorithm
# - test_calc_prerequisite: Foundational content detection
# - test_generate_reasoning: Priority reasoning generation
# - test_content_processing_flow: End-to-end upload → topics → embedding
```

### 11.4 Test Configuration

`pytest.ini` settings:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

---

## 12. Technical Notes

### 12.1 Gemini SDK

The project uses the modern `google-genai` SDK (not the deprecated `google-generativeai`).

```python
# Correct import
from google import genai

# Initialize client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Generate content
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt
)

# Generate embeddings
result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=text
)
```

### 12.2 Available Models

As of January 2025, use these models:
- **Text generation**: `gemini-2.5-flash` (recommended for speed/cost)
- **Embeddings**: `gemini-embedding-001` (3072 dimensions)

Note: `gemini-1.5-flash` is NOT available via the `google-genai` SDK v1beta API. Use `gemini-2.5-flash` instead.

### 12.3 Lazy Client Pattern

Tools use lazy initialization to allow unit tests to mock the client:

```python
_client = None

def _get_genai_client():
    """Get or create the Gemini client lazily."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client
```

### 12.4 Async-to-Sync Bridge

ADK tools are synchronous but need to call async database/API code:

```python
def _run_async(coro):
    """Run async coroutine safely, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)
```

### 12.5 Python Version

The project targets **Python 3.13** in Docker containers. For local development, Python 3.9+ works but shows deprecation warnings from google-auth.

---

## 13. E2E Smoke Test Script

A single script exists to validate the full gateway + agents + workers flow:

```bash
./scripts/test/test-e2e-smoke.sh
```

What it checks:
- Gateway health
- Profile create/get (allocates a stable session per user)
- Upload sample file
- Priority queue (longer timeout; may take 20-60s)
- Async generation + polling until complete
- Notifications fetch

Session policy:
- **One user = one session** (session id is deterministic from `user_id`), created on profile creation and reused thereafter.
