# Tips for Reading tools.py Files

## 🎯 Quick Navigation Strategy

When you open a `tools.py` file, follow this reading order:

### 1. **Start at the Top: Imports (Lines 1-20)**
```python
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import asyncpg
from google import genai
```

**What to look for:**
- `asyncpg` → Database operations
- `httpx` → HTTP calls to other agents
- `google.genai` → Gemini API calls
- `redis` → Job queue/caching
- Custom imports → Helper utilities

**Tip:** The imports tell you what the agent does:
- Database imports → Data storage/retrieval
- HTTP imports → Inter-agent communication
- AI imports → Content generation

---

### 2. **Find the Public Functions (The Tools)**

Public functions are what the AI agent can call. They follow this pattern:

```python
def tool_name(param1: str, param2: int) -> Dict[str, Any]:
    """
    Docstring explaining what this tool does.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        Dict with status and data
    """
    return _run_async(_tool_name_async(param1, param2))
```

**How to identify them:**
- ✅ No underscore prefix (e.g., `detect_changes`)
- ✅ Has detailed docstring
- ✅ Type hints for all parameters
- ✅ Returns `Dict[str, Any]`
- ✅ Usually calls `_run_async()` wrapper

**Tip:** These are the "hands" of the agent - what it can actually do!

---

### 3. **Understand the Async Pattern**

Most tools follow this two-function pattern:

```python
# Public sync wrapper (what AI calls)
def detect_changes(user_id: str) -> Dict[str, Any]:
    """Docstring for AI"""
    return _run_async(_detect_changes_async(user_id))

# Private async implementation (actual work)
async def _detect_changes_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        # Actual database/API work here
        result = await conn.fetch(...)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
```

**Why this pattern?**
- ADK expects synchronous functions
- Database/API calls are async for performance
- `_run_async()` bridges the gap

**Tip:** Always read the `_async` version to understand what actually happens!

---

## 🔍 Reading Strategies

### Strategy 1: **Follow the Data Flow**

Pick one tool and trace what happens to the data:

```python
def schedule_generation(user_id: str, job_type: str, ...) -> Dict[str, Any]:
    # 1. What comes in? user_id, job_type, content_id
    
    return _run_async(_schedule_generation_async(...))
    # 2. Where does it go? To the async function

async def _schedule_generation_async(...):
    # 3. What happens to it?
    # - Inserted into database
    # - Sent to another agent
    # - Transformed/processed
    
    # 4. What comes out?
    return {"status": "success", "job_id": "..."}
```

**Exercise:** Pick `generate_5min_summary` and trace:
1. Input: `user_id`, `content_id`, `style_dna`
2. Process: Fetch content → Build prompt → Call Gemini → Store artifact
3. Output: `{"status": "success", "artifact_id": "...", "content": "..."}`

---

### Strategy 2: **Identify the "Verbs"**

Tools are actions. Look for the verb in the function name:

| Function Name | Verb | What It Does |
|---------------|------|--------------|
| `detect_changes` | detect | Checks database for new content |
| `schedule_generation` | schedule | Creates job + calls Synthesis |
| `get_job_status` | get | Retrieves job from database |
| `create_notification` | create | Inserts notification record |
| `generate_embedding` | generate | Calls Gemini embedding API |
| `ingest_content` | ingest | Parses + stores content |

**Tip:** The verb tells you the primary action!

---

### Strategy 3: **Look for External Calls**

Tools interact with external systems. Scan for these patterns:

#### **Database Calls:**
```python
# PostgreSQL queries
await conn.fetch("SELECT * FROM table WHERE ...")
await conn.fetchrow("SELECT * FROM table WHERE ...")
await conn.execute("INSERT INTO table ...")
```

#### **API Calls:**
```python
# Gemini API
client.models.generate_content(model="gemini-2.5-flash", contents=...)
client.models.embed_content(model="gemini-embedding-001", contents=...)

# HTTP to other agents
await client.post(f"{synthesis_url}/run_sse", json=...)
```

#### **Redis/Queue:**
```python
await redis.lpush("queue_name", data)
await redis.brpop("queue_name")
```

**Tip:** These are the "integration points" - where the agent talks to the outside world!

---

## 🧩 Common Patterns to Recognize

### Pattern 1: **Database Connection Management**

```python
async def _some_tool_async(...):
    conn = await _get_db_connection()  # Get connection
    try:
        # Do work
        result = await conn.fetch(...)
        return {"status": "success", ...}
    except Exception as e:
        logger.exception("Tool failed")
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()  # Always close!
```

**Why this matters:**
- Prevents connection leaks
- Ensures cleanup even on errors
- Standard pattern across all tools

---

### Pattern 2: **Structured Return Values**

```python
# Success
{
    "status": "success",
    "data_field": value,
    "another_field": value
}

# Error
{
    "status": "error",
    "error": "Error message"
}
```

**Why this matters:**
- AI can reliably parse results
- Consistent error handling
- Easy to extend

---

### Pattern 3: **Lazy Initialization**

```python
_client = None  # Global variable

def _get_genai_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        _client = genai.Client(api_key=api_key)
    return _client
```

**Why this matters:**
- Client created only when needed
- Reused across multiple calls
- Avoids initialization overhead

---

### Pattern 4: **Parallel Execution**

```python
# Run multiple async operations in parallel
topics_task = extract_topics(content_text)
embedding_task = generate_embedding(content_text)

# Wait for both to complete
topics_result, embedding_result = await asyncio.gather(topics_task, embedding_task)
```

**Why this matters:**
- Faster execution (parallel vs sequential)
- Efficient use of I/O wait time
- Common in ingestion/processing

---

## 🎨 Visual Reading Guide

When you open a `tools.py` file, mentally divide it into sections:

```
┌─────────────────────────────────────┐
│ IMPORTS & SETUP (Lines 1-50)       │
│ - Dependencies                      │
│ - Logging config                    │
│ - Global variables                  │
│ - Helper functions                  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ TOOL 1: detect_changes              │
│ - Public function                   │
│ - Private async implementation      │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ TOOL 2: schedule_generation         │
│ - Public function                   │
│ - Private async implementation      │
│ - Helper: _run_synthesis_5min       │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ TOOL 3: get_job_status              │
│ - Public function                   │
│ - Private async implementation      │
└─────────────────────────────────────┘
```

---

## 🔧 Practical Tips

### Tip 1: **Start with the Docstrings**

```python
def schedule_generation(
    user_id: str,
    job_type: str,
    content_id: Optional[str] = None,
    priority: str = "NORMAL"
) -> Dict[str, Any]:
    """
    Schedule content for background generation.  # ← What it does
    
    Args:
        user_id: User identifier                 # ← What you need
        job_type: One of generate_5min_new...    # ← Valid values
        content_id: Content UUID (optional)      # ← Optional params
        priority: HIGH, NORMAL, or LOW           # ← Constraints
    
    Returns:
        Dict with status, job_id, job_status     # ← What you get back
    """
```

**Read this first!** It tells you:
- Purpose
- Required inputs
- Optional inputs
- Expected output

---

### Tip 2: **Ignore Helper Functions on First Pass**

Functions starting with `_` are helpers. Skip them initially:

```python
def _run_async(coro):           # ← Skip on first read
def _get_db_connection():       # ← Skip on first read
def _build_system_instruction(): # ← Skip on first read

def detect_changes(...):        # ← Read this first!
def schedule_generation(...):   # ← Read this second!
```

**Come back to helpers** when you need to understand implementation details.

---

### Tip 3: **Look for Environment Variables**

```python
synthesis_url = os.getenv("SYNTHESIS_AGENT_URL", "http://synthesis-agent:8003")
fast_path = os.getenv("ORCHESTRATOR_FAST_PATH", "false").lower() == "true"
api_key = os.getenv("GEMINI_API_KEY", "")
```

**These are configuration points!** They tell you:
- What can be customized
- Default values
- External dependencies

---

### Tip 4: **Trace Error Handling**

```python
try:
    # Happy path
    result = await conn.fetch(...)
    return {"status": "success", "data": result}
except Exception as e:
    # Error path
    logger.exception("Tool failed")
    return {"status": "error", "error": str(e)}
finally:
    # Cleanup path
    await conn.close()
```

**Ask yourself:**
- What can go wrong?
- How are errors reported?
- What cleanup happens?

---

### Tip 5: **Count the Database Queries**

```python
async def _schedule_generation_async(...):
    # Query 1: Insert job
    await conn.fetchrow("INSERT INTO background_jobs ...")
    
    # Query 2: Update job status
    await conn.execute("UPDATE background_jobs SET status = 'RUNNING' ...")
    
    # Query 3: Update job completion
    await conn.execute("UPDATE background_jobs SET status = 'COMPLETED' ...")
    
    # Query 4: Insert notification
    await conn.execute("INSERT INTO notifications ...")
```

**Why this matters:**
- Performance implications (4 queries = 4 round trips)
- Transaction boundaries
- Potential optimization opportunities

---

## 🎯 Quick Reference Checklist

When reading a new `tools.py` file, ask:

- [ ] **What external systems does it interact with?**
  - Database? Which tables?
  - APIs? Which endpoints?
  - Other agents? Which ones?

- [ ] **What are the main tools (public functions)?**
  - List them out
  - What does each do?

- [ ] **What data does it read?**
  - From database?
  - From API responses?
  - From other agents?

- [ ] **What data does it write?**
  - To database?
  - To other agents?
  - To external APIs?

- [ ] **What can fail?**
  - Network errors?
  - Database errors?
  - Validation errors?

- [ ] **How are errors handled?**
  - Logged?
  - Returned to caller?
  - Retried?

---

## 📊 Example: Reading Orchestrator tools.py

Let's apply these tips to the Orchestrator:

### Step 1: Scan Imports
```python
import asyncpg    # → Database operations
import httpx      # → HTTP calls to other agents
import json       # → Data serialization
import logging    # → Logging
```

**Conclusion:** This agent talks to database and other agents.

---

### Step 2: List Public Tools
```python
def detect_changes(...)         # Check for new content
def schedule_generation(...)    # Queue generation jobs
def get_job_status(...)         # Check job progress
def get_notifications(...)      # Fetch user notifications
def get_badge_count(...)        # Count unread notifications
def mark_notification_read(...) # Mark notification as read
def create_notification(...)    # Create new notification
```

**Conclusion:** This agent manages jobs and notifications.

---

### Step 3: Identify External Calls

**Database tables used:**
- `background_jobs` (read/write)
- `notifications` (read/write)
- `user_materials` (read)

**Agents called:**
- Synthesis Agent (`http://synthesis-agent:8003/run_sse`)

**Conclusion:** Orchestrator coordinates between database and Synthesis Agent.

---

### Step 4: Trace One Tool End-to-End

**`schedule_generation`:**
1. **Input:** `user_id`, `job_type`, `content_id`, `priority`
2. **Process:**
   - Insert job into `background_jobs` table
   - Call Synthesis Agent via HTTP
   - Wait for completion
   - Update job status
   - Create notification
3. **Output:** `{"status": "success", "job_id": "...", "job_status": "COMPLETED"}`

**Conclusion:** It's a synchronous orchestration function.

---

## 💡 Pro Tips

### 1. **Use Your IDE's "Go to Definition"**
When you see `_run_synthesis_5min(...)`, jump to its definition to understand what it does.

### 2. **Search for SQL Keywords**
Search for `SELECT`, `INSERT`, `UPDATE` to find all database operations.

### 3. **Search for `await client.post`**
Find all HTTP calls to other services.

### 4. **Look for `logger.info` and `logger.exception`**
These show you what the agent considers important or error-prone.

### 5. **Check for `os.getenv`**
These are your configuration knobs - what you can change without code changes.

---

## 🚀 Practice Exercise

Pick any `tools.py` file and answer:

1. What are the 3 main tools (public functions)?
2. Which external systems does it interact with?
3. Pick one tool and trace its data flow from input to output
4. What can go wrong in that tool?
5. How are errors handled?

**Example with Synthesis Agent:**

1. **Main tools:** `generate_artifact`, `generate_5min_summary`, `get_artifact`, `list_artifacts`
2. **External systems:** PostgreSQL (content_items, artifacts), Gemini API
3. **Data flow for `generate_5min_summary`:**
   - Input: `user_id`, `content_id`, `style_dna`
   - Fetch content from database
   - Build personalized prompt
   - Call Gemini API
   - Store result in artifacts table
   - Output: `{"status": "success", "artifact_id": "...", "content": "..."}`
4. **What can fail:** Content not found, Gemini API error, database error
5. **Error handling:** Try/except blocks, return `{"status": "error", "error": "..."}`, logging

---

## 📚 Summary

**Reading `tools.py` is like reading a recipe:**
- **Ingredients** = Imports and parameters
- **Steps** = Function implementation
- **Result** = Return value

**Key takeaways:**
1. Start with public functions (no underscore)
2. Read docstrings first
3. Trace data flow
4. Identify external calls
5. Understand error handling

Happy code reading! 🎉
