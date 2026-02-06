# Testing Agent Behavior in StudySync AI

## 🎯 Quick Overview

You have **5 ADK agents** running that you can test:
1. **Ingestion Agent** (port 8001) - Parses uploaded content
2. **Profile Agent** (port 8002) - Manages user preferences
3. **Synthesis Agent** (port 8003) - Generates study materials
4. **Planner Agent** (port 8004) - Creates learning plans
5. **Orchestrator Agent** (port 8005) - Coordinates background tasks

---

## 🌐 Method 1: Test via Frontend (Easiest)

Your fullstack dev server is running, so you can test agents through the UI:

### 1. Upload Content (Tests Ingestion Agent)
```
1. Go to http://localhost:3000
2. Navigate to Dashboard
3. Upload a PDF or paste text
4. Watch the ingestion process
```

**What happens:**
- Frontend calls `/api/v1/upload`
- Gateway forwards to **Ingestion Agent**
- Agent parses content, extracts topics, creates embeddings
- Content appears in your Knowledge Bank

### 2. Set Learning Preferences (Tests Profile Agent)
```
1. Go to http://localhost:3000/onboarding
2. Select your preferences:
   - Content formats (audio, video, notes)
   - Learning styles (analogies, real-world examples, etc.)
   - Cognitive tone (textbook, coaching, etc.)
3. Click "Save & Continue"
```

**What happens:**
- Frontend calls `/api/v1/settings/{user_id}`
- Gateway stores preferences in database
- **Profile Agent** uses these for personalization

### 3. Generate Study Materials (Tests Synthesis Agent)
```
1. After uploading content
2. Wait for automatic generation (5-min summary)
3. Or manually request generation
4. View generated artifacts
```

**What happens:**
- Background job triggers **Synthesis Agent**
- Agent generates personalized content based on your DNA
- Creates flashcards, summaries, quizzes, etc.

### 4. Generate Learning Plans (Tests Planner Agent)
```
1. Go to Learning Plans page
2. Click "Generate Suggested Plans"
3. View AI-generated study plans
```

**What happens:**
- Frontend calls `/api/v1/learning-plans/generate-suggested`
- Gateway forwards to **Planner Agent**
- Agent analyzes your content and creates structured plans

---

## 🔧 Method 2: Test via API (Direct Testing)

Use curl or Postman to test agents directly:

### Test Ingestion Agent
```bash
# Upload a file
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=test_user_123" \
  -F "files=@/path/to/your/file.pdf"

# Check upload status
curl http://localhost:8000/api/v1/upload/status/{task_id}
```

### Test Settings/Profile
```bash
# Get user settings
curl http://localhost:8000/api/v1/settings/test_user_123

# Update settings
curl -X PATCH http://localhost:8000/api/v1/settings/test_user_123 \
  -H "Content-Type: application/json" \
  -d '{
    "study_preferences": {
      "formats": ["audio", "notes"],
      "preferences": ["analogies", "practice_set"],
      "cognitive_tone": "coaching"
    }
  }'
```

### Test Learning Plan Generation
```bash
# Generate suggested plans
curl -X POST "http://localhost:8000/api/v1/learning-plans/generate-suggested?user_id=test_user_123&max_plans=3"

# List learning plans
curl "http://localhost:8000/api/v1/learning-plans?user_id=test_user_123"
```

### Test Notes Creation (Triggers Synthesis)
```bash
# Create a note (triggers background generation)
curl -X POST http://localhost:8000/api/v1/notes \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_123",
    "note_type": "text",
    "title": "Machine Learning Basics",
    "description": "Introduction to supervised and unsupervised learning"
  }'
```

---

## 🧪 Method 3: Run Unit Tests

Test individual agents with pytest:

### Test All Agents
```bash
# From project root
source .venv/bin/activate
pytest tests/ -v
```

### Test Specific Agents
```bash
# Test Ingestion Agent
pytest tests/test_ingestion_agent.py -v

# Test Profile Agent
pytest tests/test_profile_agent.py -v

# Test Synthesis Agent
pytest tests/test_synthesis_agent.py -v

# Test Planner Agent
pytest tests/test_planner_agent.py -v

# Test Orchestrator Agent
pytest tests/test_orchestrator_agent.py -v
```

### Test with Output
```bash
# See detailed output
pytest tests/test_synthesis_agent.py -v -s

# Run specific test
pytest tests/test_synthesis_agent.py::test_generate_flashcards -v
```

---

## 🔍 Method 4: Check Agent Logs

Monitor what agents are doing in real-time:

### View Agent Logs
```bash
# View all agent logs
docker-compose logs -f

# View specific agent
docker-compose logs -f synthesis-agent
docker-compose logs -f ingestion-agent
docker-compose logs -f planner-agent
docker-compose logs -f profile-agent
docker-compose logs -f orchestrator-agent

# View last 50 lines
docker-compose logs --tail=50 synthesis-agent
```

### Check Agent Status
```bash
# Check if agents are running
docker-compose ps

# Should see:
# - ingestion-agent (port 8001)
# - profile-agent (port 8002)
# - synthesis-agent (port 8003)
# - planner-agent (port 8004)
# - orchestrator-agent (port 8005)
```

---

## 🎬 Method 5: Integration Testing

Test the full workflow end-to-end:

### Full User Journey Test
```bash
# Run integration tests
GEMINI_API_KEY=your-key pytest tests/test_integration.py -v
```

### Manual Integration Test
```bash
# 1. Upload content
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=integration_test" \
  -F "files=@sample.pdf"

# 2. Wait a few seconds, then check artifacts
curl "http://localhost:8000/api/v1/artifacts?user_id=integration_test"

# 3. Generate learning plan
curl -X POST "http://localhost:8000/api/v1/learning-plans/generate-suggested?user_id=integration_test"

# 4. Check notifications
curl "http://localhost:8000/api/v1/notifications?user_id=integration_test"
```

---

## 📊 Method 6: Monitor Agent Behavior

### Check Agent Health
```bash
# Gateway health (includes Redis status)
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"gateway","redis":"connected"}
```

### Check Background Jobs
```bash
# View queue status
curl "http://localhost:8000/api/v1/queue?user_id=test_user_123"

# View processing jobs
curl "http://localhost:8000/api/v1/ingestion/processing?user_id=test_user_123"
```

### Database Inspection
```bash
# Connect to database
docker exec -it study_sync_ai-supabase-1 psql -U postgres

# Check tables
\dt

# View recent artifacts
SELECT id, artifact_type, created_at FROM artifacts ORDER BY created_at DESC LIMIT 10;

# View user settings
SELECT user_id, study_preferences FROM user_settings;

# Exit
\q
```

---

## 🎯 Recommended Testing Flow

### For Quick Testing (5 minutes)
1. ✅ Open http://localhost:3000
2. ✅ Upload a small text file or PDF
3. ✅ Set your DNA preferences
4. ✅ Wait for automatic generation
5. ✅ Check artifacts page

### For Thorough Testing (15 minutes)
1. ✅ Run unit tests: `pytest tests/test_synthesis_agent.py -v`
2. ✅ Upload content via frontend
3. ✅ Monitor logs: `docker-compose logs -f synthesis-agent`
4. ✅ Test API directly with curl
5. ✅ Generate learning plan
6. ✅ Check database for results

### For Agent Development (30+ minutes)
1. ✅ Run all tests: `pytest tests/ -v`
2. ✅ Test each agent individually
3. ✅ Monitor all agent logs
4. ✅ Test edge cases (large files, invalid input)
5. ✅ Check error handling
6. ✅ Verify personalization works with different DNA settings

---

## 🐛 Debugging Tips

### Agent Not Responding?
```bash
# Restart specific agent
docker-compose restart synthesis-agent

# Rebuild and restart
docker-compose up -d --build synthesis-agent
```

### Check Agent Connectivity
```bash
# Test if agent is reachable
curl http://localhost:8001/health  # Ingestion
curl http://localhost:8002/health  # Profile
curl http://localhost:8003/health  # Synthesis
curl http://localhost:8004/health  # Planner
curl http://localhost:8005/health  # Orchestrator
```

### View Detailed Errors
```bash
# Check gateway logs for agent communication errors
docker-compose logs gateway | grep -i error

# Check specific agent errors
docker-compose logs synthesis-agent | grep -i error
```

---

## 📝 Example Test Scenarios

### Scenario 1: Test Personalization
```bash
# 1. Set DNA to "Textbook" tone
curl -X PATCH http://localhost:8000/api/v1/settings/test_user \
  -H "Content-Type: application/json" \
  -d '{"study_preferences": {"cognitive_tone": "textbook"}}'

# 2. Upload content
curl -X POST http://localhost:8000/api/v1/upload \
  -F "user_id=test_user" \
  -F "files=@sample.txt"

# 3. Check generated content tone
curl "http://localhost:8000/api/v1/artifacts?user_id=test_user"
```

### Scenario 2: Test Learning Plan Generation
```bash
# 1. Upload multiple pieces of content
# 2. Generate plans
curl -X POST "http://localhost:8000/api/v1/learning-plans/generate-suggested?user_id=test_user&max_plans=3"

# 3. Verify plans are personalized
curl "http://localhost:8000/api/v1/learning-plans?user_id=test_user"
```

---

## 🎓 Next Steps

1. **Start with Frontend Testing** - Easiest way to see agents in action
2. **Monitor Logs** - Watch what agents do in real-time
3. **Run Unit Tests** - Verify individual agent functionality
4. **Test API Directly** - Fine-grained control over inputs
5. **Integration Testing** - Verify full workflow

Your agents are already running and ready to test! 🚀
