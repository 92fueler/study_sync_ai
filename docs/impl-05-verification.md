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

# Ingestion Agent
curl http://localhost:8001/health
# Expected: {"status": "healthy"}

# Profile Agent
curl http://localhost:8002/health
# Expected: {"status": "healthy"}

# Synthesis Agent
curl http://localhost:8003/health
# Expected: {"status": "healthy"}

# Planner Agent
curl http://localhost:8004/health
# Expected: {"status": "healthy"}

# Orchestrator Agent
curl http://localhost:8005/health
# Expected: {"status": "healthy"}

# Redis
docker-compose exec redis redis-cli ping
# Expected: PONG

# Supabase
docker-compose exec supabase pg_isready
# Expected: accepting connections
```

### 1.3 Agent Card Discovery

```bash
# Verify each agent exposes its Agent Card
curl http://localhost:8001/.well-known/agent.json | jq .name
# Expected: "ingestion-agent"

curl http://localhost:8002/.well-known/agent.json | jq .name
# Expected: "profile-agent"

curl http://localhost:8003/.well-known/agent.json | jq .name
# Expected: "synthesis-agent"

curl http://localhost:8004/.well-known/agent.json | jq .name
# Expected: "planner-agent"

curl http://localhost:8005/.well-known/agent.json | jq .name
# Expected: "orchestrator-agent"
```

---

## 2. A2A Communication Tests

### 2.1 Basic Task Send

Test that gateway can send a task to each agent:

```bash
# Test Ingestion Agent
curl -X POST http://localhost:8001/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "params": {
      "id": "test-task-1",
      "message": {
        "role": "user",
        "parts": [{"text": "{\"action\": \"ping\"}"}]
      }
    }
  }'
# Expected: {"jsonrpc": "2.0", "result": {"status": "completed", ...}}
```

### 2.2 Inter-Agent Communication

Verify agents can communicate with each other:

```bash
# Gateway orchestrates: Profile → Planner flow
curl -X POST http://localhost:8000/api/v1/test/a2a-chain \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'
# Expected: Returns combined result from multiple agents
```

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
curl http://localhost:8000/api/v1/materials?user_id=test-user
# Expected: List includes the uploaded file
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
# Generate artifact for user
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
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
# Expected: Same artifact data

# Check database
docker-compose exec supabase psql -U postgres -d studysync \
  -c "SELECT id, artifact_type, estimated_minutes FROM artifacts WHERE user_id = 'test-user';"
# Expected: Shows generated artifacts
```

### 5.3 Priority Queue

```bash
# Get prioritized queue
curl http://localhost:8000/api/v1/queue?user_id=test-user
# Expected: List of content with priority scores and reasoning
```

---

## 6. Background Generation Test

### 6.1 Job Queue

```bash
# Manually enqueue a job
curl -X POST http://localhost:8005/api/v1/jobs/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "job_type": "generate_5min_new",
    "content_id": "some-content-id"
  }'
# Expected: 200 OK with job_id

# Check job status
curl http://localhost:8005/api/v1/jobs/{job_id}/status
# Expected: "QUEUED" then "RUNNING" then "COMPLETED"
```

### 6.2 Auto-Detection

```bash
# Upload new content
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=test-user" \
  -F "files=@another-test.txt"

# Wait for orchestrator to detect (5 min poll interval or trigger manually)
# Check for auto-queued job
curl http://localhost:8005/api/v1/jobs?user_id=test-user&status=QUEUED
# Expected: Job auto-created for new content
```

### 6.3 Throttling

```bash
# Rapidly enqueue many jobs
for i in {1..10}; do
  curl -X POST http://localhost:8005/api/v1/jobs/enqueue \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"test-user\", \"job_type\": \"generate_5min_new\", \"content_id\": \"content-$i\"}"
done

# Check concurrent running jobs (max 3 per user)
curl http://localhost:8005/api/v1/jobs?user_id=test-user&status=RUNNING | jq length
# Expected: <= 3
```

---

## 7. Notification Test

```bash
# Complete a generation
# ... (run generation flow)

# Check for notification created
curl http://localhost:8000/api/v1/notifications?user_id=test-user
# Expected: Notification about artifact ready

# Check badge count
curl http://localhost:8000/api/v1/notifications/badge?user_id=test-user
# Expected: {"unread_count": 1}
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
