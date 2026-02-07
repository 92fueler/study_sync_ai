# Orchestrator Functions Explained

## 🎯 Overview

The Orchestrator Agent has **7 main tools** that manage background jobs and notifications. Think of it as the **project manager** that coordinates work between agents.

---

## 🛠️ The 7 Tools

### 1. `detect_changes` - Check for New Work
### 2. `schedule_generation` - Create & Execute Jobs
### 3. `get_job_status` - Monitor Job Progress
### 4. `get_notifications` - Fetch User Notifications
### 5. `get_badge_count` - Count Unread Notifications
### 6. `mark_notification_read` - Mark Notification as Read
### 7. `create_notification` - Send New Notification

---

## 📚 Detailed Breakdown

### 1️⃣ `detect_changes(user_id)` - The Scanner

**Purpose:** Check if there's new content or pending work for a user

**What it does:**
```python
def detect_changes(user_id: str) -> Dict[str, Any]:
    # 1. Query database for unprocessed materials
    # 2. Count pending background jobs
    # 3. Return summary
```

**Step-by-step:**

```
┌─────────────────────────────────────┐
│ 1. Connect to database              │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Query: SELECT content_id         │
│    FROM user_materials               │
│    WHERE user_id = 'user_123'       │
│    AND status = 'UNPROCESSED'       │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 3. Query: SELECT COUNT(*)           │
│    FROM background_jobs              │
│    WHERE user_id = 'user_123'       │
│    AND status IN ('QUEUED','RUNNING')│
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 4. Return result                    │
│    {                                │
│      "status": "success",           │
│      "new_content": [...],          │
│      "pending_jobs": 2              │
│    }                                │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# AI calls this to check if there's work to do
result = detect_changes(user_id="user_123")

# Returns:
{
    "status": "success",
    "new_content": [
        {"content_id": "abc-123", "uploaded_at": "2024-02-06T10:00:00Z"}
    ],
    "profile_updated": False,
    "pending_jobs": 0
}
```

**When to use:**
- User asks "Do I have new content?"
- System checks for pending work
- Before scheduling new jobs

---

### 2️⃣ `schedule_generation(...)` - The Executor

**Purpose:** Create a job AND execute it (calls Synthesis Agent)

**What it does:**
```python
def schedule_generation(
    user_id: str,
    job_type: str,           # "generate_5min_new", "generate_full_new", etc.
    content_id: str = None,  # Optional content UUID
    priority: str = "NORMAL" # "HIGH", "NORMAL", or "LOW"
) -> Dict[str, Any]:
    # 1. Insert job into database
    # 2. Call Synthesis Agent to do the work
    # 3. Update job status
    # 4. Create notification
```

**Step-by-step (Normal Path):**

```
┌─────────────────────────────────────┐
│ 1. INSERT INTO background_jobs      │
│    VALUES (user_id, job_type, ...)  │
│    → Returns job_id                 │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. UPDATE background_jobs           │
│    SET status = 'RUNNING'           │
│    WHERE id = job_id                │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 3. Call Synthesis Agent             │
│    POST http://synthesis-agent:8003 │
│    → Wait for generation (10-30s)   │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 4. UPDATE background_jobs           │
│    SET status = 'COMPLETED'         │
│    WHERE id = job_id                │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 5. INSERT INTO notifications        │
│    VALUES ('Materials ready', ...)  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 6. Return result                    │
│    {"status": "success",            │
│     "job_id": "...",                │
│     "job_status": "COMPLETED"}      │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# User uploads a PDF
result = schedule_generation(
    user_id="user_123",
    job_type="generate_5min_new",
    content_id="abc-123",
    priority="NORMAL"
)

# Returns:
{
    "status": "success",
    "job_id": "job-456",
    "job_status": "COMPLETED"
}
```

**Job Types:**
- `generate_5min_new` - Quick summary for new content
- `generate_full_new` - Full study notes for new content
- `regenerate_existing` - User requested re-generation
- `recalc_priority` - Update priority queue
- `send_notification` - Send alert

**Fast Path Mode:**
```python
# If ORCHESTRATOR_FAST_PATH=true
# Skips calling Synthesis Agent, just marks job as done
# Useful for testing
```

---

### 3️⃣ `get_job_status(job_id)` - The Monitor

**Purpose:** Check the status of a background job

**What it does:**
```python
def get_job_status(job_id: str) -> Dict[str, Any]:
    # Query database for job details
    # Return status, timestamps, error messages
```

**Step-by-step:**

```
┌─────────────────────────────────────┐
│ 1. SELECT * FROM background_jobs    │
│    WHERE id = 'job-456'             │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Return job details               │
│    {                                │
│      "job_id": "job-456",           │
│      "job_status": "COMPLETED",     │
│      "job_type": "generate_5min",   │
│      "created_at": "...",           │
│      "completed_at": "..."          │
│    }                                │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# Check if generation is done
result = get_job_status(job_id="job-456")

# Returns:
{
    "status": "success",
    "job_id": "job-456",
    "job_status": "COMPLETED",  # or "QUEUED", "RUNNING", "FAILED"
    "job_type": "generate_5min_new",
    "priority": "NORMAL",
    "attempts": 1,
    "created_at": "2024-02-06T10:00:00Z",
    "started_at": "2024-02-06T10:00:01Z",
    "completed_at": "2024-02-06T10:00:15Z",
    "error_message": None
}
```

**Job Statuses:**
- `QUEUED` - Job created, waiting to run
- `RUNNING` - Currently executing
- `COMPLETED` - Successfully finished
- `FAILED` - Error occurred

---

### 4️⃣ `get_notifications(user_id, unread_only)` - The Inbox

**Purpose:** Fetch notifications for a user

**What it does:**
```python
def get_notifications(
    user_id: str,
    unread_only: bool = False  # If True, only return unread
) -> Dict[str, Any]:
    # Query notifications table
    # Return list of notifications
```

**Step-by-step:**

```
┌─────────────────────────────────────┐
│ 1. SELECT * FROM notifications      │
│    WHERE user_id = 'user_123'       │
│    AND read = FALSE (if unread_only)│
│    ORDER BY created_at DESC         │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Return list of notifications     │
│    [                                │
│      {                              │
│        "id": "notif-1",             │
│        "title": "Materials ready",  │
│        "body": "Your summary...",   │
│        "read": false,               │
│        "created_at": "..."          │
│      }                              │
│    ]                                │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# Get all notifications
result = get_notifications(user_id="user_123", unread_only=False)

# Returns:
{
    "status": "success",
    "notifications": [
        {
            "id": "notif-1",
            "title": "Materials ready",
            "body": "Your 5-minute summary is ready.",
            "data": {"job_id": "job-456", "status": "ready"},
            "read": False,
            "created_at": "2024-02-06T10:00:15Z"
        },
        {
            "id": "notif-2",
            "title": "Upload complete",
            "body": "machine_learning.pdf processed successfully.",
            "data": {"content_id": "abc-123"},
            "read": True,
            "created_at": "2024-02-06T09:55:00Z"
        }
    ]
}
```

---

### 5️⃣ `get_badge_count(user_id)` - The Counter

**Purpose:** Count unread notifications (for badge display)

**What it does:**
```python
def get_badge_count(user_id: str) -> Dict[str, Any]:
    # Count unread notifications
    # Return number
```

**Step-by-step:**

```
┌─────────────────────────────────────┐
│ 1. SELECT COUNT(*) FROM notifications│
│    WHERE user_id = 'user_123'       │
│    AND read = FALSE                 │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Return count                     │
│    {"unread_count": 3}              │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# Get badge count for UI
result = get_badge_count(user_id="user_123")

# Returns:
{
    "status": "success",
    "unread_count": 3
}

# Frontend displays: 🔔 (3)
```

---

### 6️⃣ `mark_notification_read(notification_id)` - The Marker

**Purpose:** Mark a notification as read

**What it does:**
```python
def mark_notification_read(notification_id: str) -> Dict[str, Any]:
    # Update notification.read = TRUE
```

**Step-by-step:**

```
┌─────────────────────────────────────┐
│ 1. UPDATE notifications             │
│    SET read = TRUE                  │
│    WHERE id = 'notif-1'             │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Return success                   │
│    {"status": "success"}            │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# User clicks on notification
result = mark_notification_read(notification_id="notif-1")

# Returns:
{
    "status": "success"
}

# Badge count decreases: 🔔 (2)
```

---

### 7️⃣ `create_notification(...)` - The Sender

**Purpose:** Create a new notification for a user

**What it does:**
```python
def create_notification(
    user_id: str,
    title: str,
    body: str,
    channel: str = "in_app",  # "push", "in_app", or "email"
    data: Dict = None         # Optional metadata
) -> Dict[str, Any]:
    # Insert notification into database
```

**Step-by-step:**

```
┌─────────────────────────────────────┐
│ 1. INSERT INTO notifications        │
│    VALUES (                         │
│      user_id = 'user_123',          │
│      title = 'New content ready',   │
│      body = 'Your summary...',      │
│      data = '{"artifact_id": "..."}'│
│    )                                │
│    → Returns notification_id        │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Return result                    │
│    {"notification_id": "notif-3"}   │
└─────────────────────────────────────┘
```

**Example Usage:**
```python
# Send notification when artifact is ready
result = create_notification(
    user_id="user_123",
    title="Materials ready",
    body="Your 5-minute summary is ready to view!",
    channel="in_app",
    data={"artifact_id": "art-789", "content_id": "abc-123"}
)

# Returns:
{
    "status": "success",
    "notification_id": "notif-3"
}
```

**Channels:**
- `in_app` - Shows in app notification center
- `push` - Push notification to mobile device
- `email` - Email notification

---

## 🔄 How They Work Together

### Example: User Uploads a PDF

```
1. User uploads machine_learning.pdf
   ↓
2. Gateway calls Ingestion Agent
   ↓
3. Ingestion processes → content_id = "abc-123"
   ↓
4. Gateway calls Orchestrator: detect_changes("user_123")
   → Returns: {"new_content": [{"content_id": "abc-123"}]}
   ↓
5. Orchestrator AI decides: "New content needs 5-min summary"
   ↓
6. Orchestrator calls: schedule_generation(
       user_id="user_123",
       job_type="generate_5min_new",
       content_id="abc-123"
   )
   ↓
7. schedule_generation:
   a. Creates job in database (status: QUEUED)
   b. Updates job (status: RUNNING)
   c. Calls Synthesis Agent via HTTP
   d. Synthesis generates summary
   e. Updates job (status: COMPLETED)
   f. Creates notification
   ↓
8. User sees notification: "Materials ready 📚"
   ↓
9. User clicks notification
   ↓
10. Frontend calls: mark_notification_read("notif-1")
    ↓
11. Badge count updates: 🔔 (0)
```

---

## 🎯 Key Concepts

### 1. **Synchronous Execution**
```python
# schedule_generation WAITS for Synthesis to complete
await _run_synthesis_5min(user_id, content_id)  # Blocks here
# Then continues...
```

**Pros:**
- Simple error handling
- Guaranteed completion
- Easy to debug

**Cons:**
- Orchestrator is blocked during generation
- Can't handle multiple jobs in parallel

### 2. **Database as State Store**
All job state is stored in PostgreSQL:
```sql
background_jobs table:
- id (UUID)
- user_id
- job_type
- status (QUEUED, RUNNING, COMPLETED, FAILED)
- priority (HIGH, NORMAL, LOW)
- created_at, started_at, completed_at
- error_message
```

### 3. **Notification System**
```sql
notifications table:
- id (UUID)
- user_id
- title
- body
- data (JSON metadata)
- read (boolean)
- created_at
```

---

## 💡 Common Patterns

### Pattern 1: Check Before Schedule
```python
# 1. Check for new content
changes = detect_changes(user_id="user_123")

# 2. If new content exists, schedule generation
if changes["new_content"]:
    for content in changes["new_content"]:
        schedule_generation(
            user_id="user_123",
            job_type="generate_5min_new",
            content_id=content["content_id"]
        )
```

### Pattern 2: Monitor Job Progress
```python
# 1. Schedule job
result = schedule_generation(...)
job_id = result["job_id"]

# 2. Check status
status = get_job_status(job_id)
if status["job_status"] == "COMPLETED":
    print("Generation complete!")
elif status["job_status"] == "FAILED":
    print(f"Error: {status['error_message']}")
```

### Pattern 3: Notification Flow
```python
# 1. Create notification
create_notification(
    user_id="user_123",
    title="Materials ready",
    body="Your summary is ready!"
)

# 2. User sees badge
badge = get_badge_count(user_id="user_123")
# → {"unread_count": 1}

# 3. User reads notifications
notifs = get_notifications(user_id="user_123", unread_only=True)

# 4. User clicks notification
mark_notification_read(notification_id="notif-1")

# 5. Badge updates
badge = get_badge_count(user_id="user_123")
# → {"unread_count": 0}
```

---

## 🚀 Summary

The Orchestrator is the **coordinator** that:
- ✅ Detects new work (`detect_changes`)
- ✅ Executes jobs (`schedule_generation`)
- ✅ Monitors progress (`get_job_status`)
- ✅ Manages notifications (`create_notification`, `get_notifications`, etc.)

**Key insight:** It doesn't generate content itself - it **delegates to Synthesis Agent** and manages the workflow!
