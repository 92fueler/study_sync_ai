# Ingestion Agent

The Ingestion Agent is responsible for parsing uploaded content, extracting topics, and generating embeddings for StudySync AI.

## Overview

- **Port**: 8001
- **ADK App Name**: `ingestion`
- **Purpose**: Process uploaded files (text, PDFs, etc.) and extract structured information

## Architecture

```
Gateway (port 8000)
    ↓ HTTP POST /api/v1/upload
    ↓ Creates ADK session
    ↓ Calls /run endpoint
Ingestion Agent (port 8001)
    ↓ Processes message
    ↓ Calls ingest_content tool
    ↓ Returns result
Gateway
    ↓ Returns response to client
```

## How to start 

### 1. Start Infra Services

Start Redis and Supabase using the dev script:

```bash
cd /path/to/study_sync_ai
./scripts/startup/start-dev.sh
```

The gateway will be available at `http://localhost:8000`

### 2. Start the Ingestion Agent

```bash
cd /path/to/study_sync_ai
docker-compose up -d ingestion-agent
```

Check status:
```bash
docker ps | grep ingestion-agent
docker logs study_sync_ai-ingestion-agent-1 --tail 20
```

The agent will be available at `http://localhost:8001`


## Testing

### Test 1: Verify Agent is Running

Check if the agent is accessible:

```bash
curl http://localhost:8001/health
# Should return health status or 404 (if health endpoint not available)
```

### Test 2: Create a Session

ADK requires sessions to be created before calling `/run`:

```bash
curl -X POST "http://localhost:8001/apps/ingestion/users/test-user/sessions/test-session-123" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

**Expected Response:**
```json
{
    "id": "test-session-123",
    "appName": "ingestion",
    "userId": "test-user",
    "state": {},
    "events": [],
    "lastUpdateTime": 1234567890.123
}
```

### Test 3: Call the Agent Directly

Test the agent execution endpoint:

```bash
curl -X POST "http://localhost:8001/run" \
  -H "Content-Type: application/json" \
  -d '{
    "appName": "ingestion",
    "userId": "test-user",
    "sessionId": "test-session-123",
    "newMessage": {
      "role": "user",
      "parts": [{"text": "Please ingest this content using the ingest_content tool:\n- user_id: test-user\n- content_hash: abc123\n- filename: test.txt\n- media_type: TXT\n- content_text: This is a test file"}]
    }
  }'
```

**Note**: Make sure the session exists (from Test 2) before calling `/run`.

**Expected Responses:**

✅ **Success** (if API quota available):
```json
[
  {
    "content": {...},
    "invocationId": "...",
    "author": "ingestion_agent",
    ...
  }
]
```

⚠️ **Quota Error** (if Gemini API quota exceeded - this is still a successful integration test):
```
Internal Server Error
```

Check logs to confirm it's a quota issue:
```bash
docker logs study_sync_ai-ingestion-agent-1 --tail 20 | grep -i "quota\|429\|RESOURCE_EXHAUSTED"
```

**What this means**: If you see "Internal Server Error" due to quota limits, the integration is working correctly! The agent:
1. ✅ Received the request
2. ✅ Found the session
3. ✅ Processed the message
4. ✅ Attempted to call Gemini API
5. ⚠️ Hit API quota limit (expected when quota is exceeded)

This confirms the full integration flow is working.

### Test 4: Test Upload Endpoint Integration

Test the full upload flow through the gateway:

```bash
# Create a test file
cat > /tmp/test-upload.txt << 'EOF'
React is a JavaScript library for building user interfaces.

Key Concepts:
1. Components - Reusable UI building blocks
2. Props - Data passed from parent to child
3. State - Component's internal data that can change
EOF

# Test upload endpoint
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "user_id=test-user-123" \
  -F "files=@/tmp/test-upload.txt" | python3 -m json.tool
```

**Expected Responses:**

✅ **Success** (if API quota available):
```json
{
    "user_id": "test-user-123",
    "uploaded": 1,
    "results": [
        {
            "filename": "test-upload.txt",
            "status": "processing",
            "task_id": "uuid-here",
            "content_id": "content-uuid",
            "response": {...}
        }
    ]
}
```

⚠️ **Quota Error** (if Gemini API quota exceeded - integration still working):
```json
{
    "user_id": "test-user-123",
    "uploaded": 1,
    "results": [
        {
            "filename": "test-upload.txt",
            "status": "error",
            "error": "Agent error: Internal Server Error"
        }
    ]
}
```

**What this means**: If you see an error due to quota limits, check the agent logs. The integration flow is working correctly - the error is from the Gemini API quota, not your code.

**Or use the test script:**
```bash
./scripts/test/test-upload.sh
```

### Test 5: Check Agent Logs

Monitor agent logs for debugging:

```bash
# Docker logs
docker logs study_sync_ai-ingestion-agent-1 --tail 50 -f

# Or if running locally, check the terminal output
```

## Troubleshooting notes

### "Session not found" Error

**Problem**: Getting "Session not found" when calling `/run`

**Solution**: Sessions must be created before calling `/run`. The gateway automatically creates sessions, but if testing directly:
1. Create session first: `POST /apps/ingestion/users/{user_id}/sessions/{session_id}`
2. Then call `/run` with the same `sessionId`

### "No root_agent found" Error

**Problem**: Agent fails to start with "No root_agent found"

**Solution**: 
- Ensure `agent.py` exports `root_agent`
- Check that the directory structure matches ADK expectations
- Verify `adk api_server` is run from the correct directory

### Connection Errors

**Problem**: Gateway can't connect to ingestion agent

**Solution**:
- Verify agent is running: `docker ps | grep ingestion-agent`
- Check agent logs: `docker logs study_sync_ai-ingestion-agent-1`
- Verify port 8001 is accessible: `curl http://localhost:8001`
- Check `INGESTION_AGENT_URL` in gateway config (default: `http://localhost:8001`)

### Gemini API Quota Errors

**Problem**: Getting "429 RESOURCE_EXHAUSTED" errors

**Solution**:
- This is an API quota limit, not a code issue
- Wait for quota to reset (usually 1 minute)
- Check your Gemini API quota/billing
- The integration is working correctly - this is expected when quota is exceeded



## Key Endpoints

### ADK API Server Endpoints

- `POST /apps/{app_name}/users/{user_id}/sessions/{session_id}` - Create session
- `POST /run` - Execute agent with message
- `POST /run_sse` - Execute agent with streaming (Server-Sent Events)
- `GET /apps/{app_name}/users/{user_id}/sessions/{session_id}` - Get session
- `GET /list-apps` - List available agents

### Gateway Endpoints

- `POST /api/v1/upload` - Upload files (triggers ingestion agent)
- `GET /api/v1/upload/status/{task_id}` - Check upload status
- `GET /health` - Health check
