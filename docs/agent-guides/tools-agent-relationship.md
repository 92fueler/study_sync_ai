# How tools.py Works with agent.py

## 🎯 The Big Picture

Each agent has **two key files** that work together:

1. **`tools.py`** - Defines **executable Python functions** (the "hands")
2. **`agent.py`** - Defines the **AI brain** that decides when to use those functions

Think of it like this:
- `agent.py` = **The Brain** (AI that makes decisions)
- `tools.py` = **The Hands** (actual code that does work)

---

## 🔧 How They Connect

### Step 1: tools.py Defines Functions

```python
# agents/orchestrator/tools.py

def detect_changes(user_id: str) -> Dict[str, Any]:
    """
    Detect new content or profile changes that need processing.
    
    Args:
        user_id: User identifier
    
    Returns:
        Dict with status, new_content list, profile_updated flag
    """
    logger.info("detect_changes called", extra={"user_id": user_id})
    return _run_async(_detect_changes_async(user_id))
```

**Key points:**
- Regular Python function with type hints
- Docstring explains what it does (AI reads this!)
- Returns a dictionary with results
- Can be sync or async (uses helper `_run_async`)

### Step 2: agent.py Imports and Registers Tools

```python
# agents/orchestrator/agent.py

from google.adk.agents import LlmAgent
from .tools import (
    detect_changes, schedule_generation, get_job_status,
    get_notifications, get_badge_count, mark_notification_read
)

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="orchestrator_agent",
    description="Coordinates background content generation...",
    instruction="""You are the Orchestrator Agent...""",
    tools=[
        detect_changes,           # ← Function reference (not called!)
        schedule_generation,
        get_job_status,
        # ... more tools
    ],
)
```

**Key points:**
- Imports functions from `tools.py`
- Passes function **references** (not calls) to `LlmAgent`
- ADK framework reads function signatures and docstrings
- AI learns what each tool does from the docstring

### Step 3: AI Decides When to Call Tools

When a user sends a message to the agent:

```
User: "Check if there's new content for user_123"
         ↓
    Agent (AI) thinks:
    "I need to detect changes. I have a tool called 'detect_changes'
     that takes user_id as a parameter. Let me call it!"
         ↓
    AI calls: detect_changes(user_id="user_123")
         ↓
    Python executes the actual function in tools.py
         ↓
    Returns: {"status": "success", "new_content": [...]}
         ↓
    AI reads result and responds to user
```

---

## 📚 Real Examples from Each Agent

### Example 1: Orchestrator Agent

**tools.py** (The Hands):
```python
def schedule_generation(
    user_id: str,
    job_type: str,
    content_id: Optional[str] = None,
    priority: str = "NORMAL"
) -> Dict[str, Any]:
    """
    Schedule content for background generation.
    
    Args:
        user_id: User identifier
        job_type: One of generate_5min_new, generate_full_new, etc.
        content_id: Content UUID (optional)
        priority: HIGH, NORMAL, or LOW
    
    Returns:
        Dict with status, job_id, and initial job status
    """
    # Actual implementation...
    return _run_async(_schedule_generation_async(...))
```

**agent.py** (The Brain):
```python
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="orchestrator_agent",
    instruction="""You coordinate background workflows.
    
    Your capabilities:
    1. detect_changes - Check for new uploads
    2. schedule_generation - Queue content for generation
    3. get_job_status - Monitor background jobs
    ...
    
    Job Types:
    - generate_5min_new: Quick summary for new content
    - generate_full_new: Full artifact
    - regenerate_existing: User-requested refresh
    """,
    tools=[schedule_generation, ...]  # ← Registers the function
)
```

**How they work together:**
1. User uploads a file
2. Gateway calls Orchestrator Agent: "New content uploaded for user_123"
3. AI reads instruction, sees it should use `schedule_generation`
4. AI calls: `schedule_generation(user_id="user_123", job_type="generate_5min_new", priority="NORMAL")`
5. Python function executes, inserts job into database
6. Returns: `{"status": "success", "job_id": "abc-123"}`
7. AI responds: "Scheduled 5-minute summary generation (job_id: abc-123)"

---

### Example 2: Ingestion Agent

**tools.py** (The Hands):
```python
async def ingest_content(
    user_id: str,
    content_hash: str,
    filename: str,
    media_type: str,
    content_text: str
) -> Dict[str, Any]:
    """
    Ingests content: deduplicates, extracts topics & embeddings, stores in DB.
    Returns content_id, material_id, topics, and word_count.
    """
    pool = await _get_db_pool()
    
    async with pool.acquire() as conn:
        # Check for duplicates
        existing = await conn.fetchrow(
            "SELECT id FROM content_items WHERE content_hash = $1", 
            content_hash
        )
        
        if existing:
            return {"status": "success", "content_id": str(existing["id"]), "deduplicated": True}
        
        # Extract topics and generate embeddings in parallel
        topics_task = extract_topics(content_text)
        embedding_task = generate_embedding(content_text)
        topics_result, embedding_result = await asyncio.gather(topics_task, embedding_task)
        
        # Store in database
        row = await conn.fetchrow(
            """INSERT INTO content_items 
               (content_hash, title, raw_text, media_type, embedding, topics, word_count)
               VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
               RETURNING id""",
            content_hash, filename, content_text, media_type,
            embedding_str, json.dumps(topics_result.get("topics", [])), word_count
        )
        
        return {
            "status": "success",
            "content_id": str(row["id"]),
            "topics": topics_result.get("topics", []),
            "word_count": word_count
        }
```

**agent.py** (The Brain):
```python
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="ingestion_agent",
    description="The 'Librarian' of StudySync AI. Ingests raw materials...",
    instruction="""
    CORE WORKFLOW:
    1. **Analyze Input**: Determine if input is File, URL, or Raw Text
    2. **Ingest**: Call `ingest_content` immediately to parse and store
    3. **Enrich**: 
       - Call `extract_topics` (extract concepts, not keywords)
       - Call `generate_embedding` (ensure semantic meaning)
    4. **Report**: Return valid JSON summary
    
    TOPIC EXTRACTION RULES:
    - **Hierarchy**: Identify 'Main Subject' vs 'Sub-topics'
    - **Relevance**: Ignore generic formatting
    - **Density**: Flag content < 50 words as LOW_QUALITY
    """,
    tools=[ingest_content, extract_topics, generate_embedding]
)
```

**How they work together:**
1. User uploads "machine_learning.pdf"
2. Gateway calls Ingestion Agent with file content
3. AI reads instruction, knows to call `ingest_content` first
4. AI calls: `ingest_content(user_id="user_123", content_hash="abc...", filename="machine_learning.pdf", ...)`
5. Python function:
   - Checks for duplicates
   - Extracts topics: ["Neural Networks", "Gradient Descent"]
   - Generates embeddings (vector representation)
   - Stores in database
6. Returns: `{"status": "success", "content_id": "uuid-123", "topics": [...], "word_count": 5000}`
7. AI responds with structured JSON summary

---

### Example 3: Synthesis Agent

**tools.py** (The Hands):
```python
def generate_5min_summary(
    user_id: str,
    content_id: str,
    profile_version: int,
    style_dna: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate only a 5-minute summary.
    
    Args:
        user_id: User identifier
        content_id: Single content ID to summarize
        profile_version: Profile version for cache
        style_dna: User's style preferences
    
    Returns:
        Dict with status, artifact_id, content, estimated_minutes (always 5)
    """
    return _run_async(_generate_5min_async(user_id, content_id, profile_version, style_dna))

async def _generate_5min_async(...):
    conn = await _get_db_connection()
    
    # Get source content from database
    row = await conn.fetchrow("SELECT raw_text FROM content_items WHERE id = $1", content_id)
    
    # Build personalized system instruction from Style DNA
    system_instruction = _build_system_instruction(style_dna)
    
    # Generate summary using Gemini
    prompt = f"""{system_instruction}
    
    TASK: Create a 5-minute quick summary...
    SOURCE MATERIAL: {row['raw_text'][:12000]}
    """
    
    response = _get_genai_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    # Store artifact in database
    artifact_row = await conn.fetchrow(
        """INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
           VALUES ($1, $2, $3, '5min', $4, 5)
           RETURNING id""",
        user_id, [content_id], profile_version, response.text
    )
    
    return {
        "status": "success",
        "artifact_id": str(artifact_row["id"]),
        "content": response.text,
        "estimated_minutes": 5
    }
```

**agent.py** (The Brain):
```python
root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="synthesis_agent",
    description="Generates personalized study materials...",
    instruction="""You are the Synthesis Agent for StudySync AI.
    
    CORE CAPABILITIES:
    1. Generate full study notes (15-60 minutes reading time)
    2. Generate 5-minute quick summaries
    3. Apply user Style DNA consistently (tone, format, emoji, diagrams)
    4. Maintain factual accuracy while improving clarity
    
    STYLE DNA COMPONENTS (MUST RESPECT):
    
    TONE:
    - "eli5": Simple explanations with analogies
    - "socratic": Questioning approach
    - "academic": Formal, precise, technical language
    
    For generate_5min_summary (quick summaries):
    1. Retrieve single content item
    2. Generate condensed 5-minute version only
    3. Focus on key takeaways and essential information
    4. Cache with artifact_type='5min'
    """,
    tools=[generate_artifact, generate_5min_summary, get_artifact, list_artifacts]
)
```

**How they work together:**
1. Orchestrator schedules a 5-min summary job
2. Worker calls Synthesis Agent: "Generate 5-min summary for content_id=uuid-123, user_id=user_123"
3. AI reads instruction, knows to use `generate_5min_summary`
4. AI calls: `generate_5min_summary(user_id="user_123", content_id="uuid-123", profile_version=1, style_dna={"tone": "coaching", ...})`
5. Python function:
   - Retrieves content from database
   - Builds personalized prompt based on user's DNA
   - Calls Gemini to generate summary
   - Stores artifact in database
6. Returns: `{"status": "success", "artifact_id": "art-123", "content": "# Machine Learning Summary\n\nLet's think about...", "estimated_minutes": 5}`
7. AI confirms: "Generated 5-minute summary (artifact_id: art-123)"

---

## 🔑 Key Design Patterns

### Pattern 1: Sync Wrapper for Async Functions

Many tools use this pattern:

```python
# Public sync function (what AI calls)
def detect_changes(user_id: str) -> Dict[str, Any]:
    """Docstring for AI to read"""
    return _run_async(_detect_changes_async(user_id))

# Private async implementation
async def _detect_changes_async(user_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    # Actual async work...
    return result
```

**Why?**
- ADK framework expects sync functions
- Database operations are async for performance
- `_run_async` helper bridges the gap

### Pattern 2: Descriptive Docstrings

```python
def schedule_generation(
    user_id: str,
    job_type: str,
    content_id: Optional[str] = None,
    priority: str = "NORMAL"
) -> Dict[str, Any]:
    """
    Schedule content for background generation.
    
    Args:
        user_id: User identifier
        job_type: One of generate_5min_new, generate_full_new, regenerate_existing
        content_id: Content UUID (optional, depends on job_type)
        priority: HIGH, NORMAL, or LOW
    
    Returns:
        Dict with status, job_id, and initial job status
    """
```

**Why?**
- AI reads docstrings to understand what tools do
- Clear parameter descriptions help AI use tools correctly
- Return type documentation helps AI interpret results

### Pattern 3: Structured Return Values

All tools return dictionaries with consistent structure:

```python
# Success case
{
    "status": "success",
    "data_field_1": value1,
    "data_field_2": value2
}

# Error case
{
    "status": "error",
    "error": "Error message here"
}
```

**Why?**
- AI can reliably parse results
- Consistent error handling
- Easy to extend with new fields

### Pattern 4: Database Connection Management

```python
async def _some_tool_async(...):
    conn = await _get_db_connection()
    try:
        # Do database work
        result = await conn.fetchrow(...)
        return {"status": "success", ...}
    except Exception as e:
        logger.exception("Tool failed")
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()  # Always close connection
```

**Why?**
- Prevents connection leaks
- Proper error handling
- Logging for debugging

---

## 🧠 How the AI Learns to Use Tools

### 1. Function Signature

```python
def detect_changes(user_id: str) -> Dict[str, Any]:
```

AI learns:
- Function name: `detect_changes`
- Required parameter: `user_id` (type: string)
- Returns: dictionary

### 2. Docstring

```python
"""
Detect new content or profile changes that need processing.

Args:
    user_id: User identifier

Returns:
    Dict with status, new_content list, profile_updated flag, pending_jobs count
"""
```

AI learns:
- **What it does**: Detects new content or profile changes
- **When to use it**: When checking for things that need processing
- **What it returns**: Status, new content list, flags

### 3. Agent Instruction

```python
instruction="""You are the Orchestrator Agent...

Your capabilities:
1. detect_changes - Check for new uploads or profile changes needing processing
2. schedule_generation - Queue content for background generation
...

When to use detect_changes:
- User asks "Is there new content?"
- System needs to check for pending work
- Before scheduling new generation jobs
"""
```

AI learns:
- **Context**: When this tool is appropriate
- **Examples**: Specific use cases
- **Workflow**: How tools relate to each other

---

## 🎯 Complete Workflow Example

Let's trace a complete user journey:

### User Action: Upload PDF

**1. Gateway receives upload**
```python
# gateway/app/api/v1/upload.py
@router.post("/upload")
async def upload_files(user_id: str, files: List[UploadFile]):
    # Call Ingestion Agent via ADK
    response = await a2a_client.send_message(
        app_name="ingestion",
        user_id=user_id,
        message="Process uploaded file: machine_learning.pdf"
    )
```

**2. Ingestion Agent (AI) receives message**
```
AI thinks: "I need to ingest a file. My instruction says:
'Call ingest_content immediately to parse and store the raw data.'
I have a tool called ingest_content that takes user_id, content_hash, filename, media_type, content_text.
Let me call it!"
```

**3. AI calls tool**
```python
# AI executes:
result = ingest_content(
    user_id="user_123",
    content_hash="abc...",
    filename="machine_learning.pdf",
    media_type="application/pdf",
    content_text="Neural networks are..."
)
```

**4. Python function executes (tools.py)**
```python
async def ingest_content(...):
    # Extract topics in parallel
    topics_result = await extract_topics(content_text)
    # Returns: {"topics": ["Neural Networks", "Gradient Descent"]}
    
    # Generate embeddings
    embedding_result = await generate_embedding(content_text)
    # Returns: {"embedding": [0.123, 0.456, ...], "dimensions": 768}
    
    # Store in database
    row = await conn.fetchrow("INSERT INTO content_items ...")
    
    return {
        "status": "success",
        "content_id": "uuid-123",
        "topics": ["Neural Networks", "Gradient Descent"],
        "word_count": 5000
    }
```

**5. AI receives result and responds**
```
AI: "Successfully ingested machine_learning.pdf
- Content ID: uuid-123
- Topics: Neural Networks, Gradient Descent
- Word count: 5000
- Status: Ready for synthesis"
```

**6. Gateway triggers Orchestrator**
```python
# Gateway calls Orchestrator Agent
await a2a_client.send_message(
    app_name="orchestrator",
    user_id=user_id,
    message=f"New content uploaded: {content_id}. Schedule proactive generation."
)
```

**7. Orchestrator Agent (AI) receives message**
```
AI thinks: "New content needs proactive generation. My instruction says:
'NEW content = PROACTIVE: Generate 5-min summaries immediately'
I should use schedule_generation with job_type='generate_5min_new' and priority='NORMAL'."
```

**8. AI calls tool**
```python
result = schedule_generation(
    user_id="user_123",
    job_type="generate_5min_new",
    content_id="uuid-123",
    priority="NORMAL"
)
```

**9. Python function executes (tools.py)**
```python
async def _schedule_generation_async(...):
    # Insert job into database
    row = await conn.fetchrow(
        "INSERT INTO background_jobs (user_id, job_type, payload, priority) VALUES ..."
    )
    job_id = str(row["id"])
    
    # Call Synthesis Agent
    await _run_synthesis_5min(user_id, content_id)
    
    # Create notification
    await conn.execute(
        "INSERT INTO notifications (user_id, title, body) VALUES ..."
    )
    
    return {"status": "success", "job_id": job_id, "job_status": "COMPLETED"}
```

**10. Synthesis Agent generates summary**
```python
# Orchestrator's _run_synthesis_5min calls Synthesis Agent
response = await client.post(
    f"{synthesis_url}/run_sse",
    json={
        "new_message": {
            "text": "Generate a 5-minute summary using generate_5min_summary tool..."
        }
    }
)
```

**11. Synthesis Agent (AI) receives message**
```
AI thinks: "I need to generate a 5-minute summary. I have generate_5min_summary tool.
I need to get the user's Style DNA first to personalize it."
```

**12. AI calls tool**
```python
result = generate_5min_summary(
    user_id="user_123",
    content_id="uuid-123",
    profile_version=1,
    style_dna={"tone": "coaching", "format_pref": "outline", ...}
)
```

**13. Python function executes (tools.py)**
```python
async def _generate_5min_async(...):
    # Get content
    row = await conn.fetchrow("SELECT raw_text FROM content_items WHERE id = $1", content_id)
    
    # Build personalized prompt
    system_instruction = _build_system_instruction(style_dna)
    prompt = f"{system_instruction}\n\nTASK: Create 5-min summary...\nSOURCE: {row['raw_text']}"
    
    # Call Gemini
    response = _get_genai_client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    # Store artifact
    artifact_row = await conn.fetchrow("INSERT INTO artifacts ...")
    
    return {
        "status": "success",
        "artifact_id": "art-123",
        "content": response.text,
        "estimated_minutes": 5
    }
```

**14. User gets notification**
```
Frontend polls /api/v1/notifications
Receives: "Your 5-minute summary is ready! 📚"
User clicks → Views personalized summary with coaching tone
```

---

## 📊 Summary

### tools.py Responsibilities:
- ✅ Define executable Python functions
- ✅ Handle database operations
- ✅ Call external APIs (Gemini, other agents)
- ✅ Process data and return results
- ✅ Error handling and logging

### agent.py Responsibilities:
- ✅ Import tools from tools.py
- ✅ Register tools with LlmAgent
- ✅ Provide AI instruction (context, rules, examples)
- ✅ Define agent personality and behavior

### How They Work Together:
1. **agent.py** creates an AI agent with specific instructions
2. **agent.py** registers functions from **tools.py** as available tools
3. User sends message to agent
4. **AI reads instructions** and decides which tool to use
5. **AI calls tool** from tools.py with appropriate parameters
6. **Python function executes** actual work (database, API calls, etc.)
7. **Function returns result** to AI
8. **AI interprets result** and responds to user

This separation allows:
- 🧠 **AI handles reasoning** (when to do what)
- 🔧 **Python handles execution** (how to do it)
- 🔄 **Clean separation of concerns**
- 🧪 **Easy testing** (test tools independently)
- 📝 **Clear documentation** (docstrings for both humans and AI)
