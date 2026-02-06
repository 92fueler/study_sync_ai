# StudySync AI - API Contracts Reference

Complete API contract documentation with request/response examples.

**Base URL**: `/api/v1`

---

## 📝 Notes API

### `POST /api/v1/notes`
Create a new learning note.

**Request Body**:
```json
{
  "user_id": "user_1234567890",
  "note_type": "text",
  "title": "Introduction to Machine Learning",
  "description": "Basic concepts of supervised and unsupervised learning",
  "tags": [
    {"type": "format", "label": "Notes"},
    {"type": "topic", "label": "AI"},
    {"type": "goal", "label": "Prep for midterm"}
  ],
  "author": "AI Summary",
  "topic": "Machine Learning",
  "thumbnail_url": null,
  "source_id": "content-uuid-123"
}
```

**Response** (201):
```json
{
  "id": "note-uuid-456",
  "user_id": "user_1234567890",
  "note_type": "text",
  "title": "Introduction to Machine Learning",
  "description": "Basic concepts of supervised and unsupervised learning",
  "tags": [
    {"type": "format", "label": "Notes"},
    {"type": "topic", "label": "AI"}
  ],
  "author": "AI Summary",
  "topic": "Machine Learning",
  "thumbnail_url": null,
  "source_id": "content-uuid-123",
  "created_at": "2026-02-04T16:30:00Z"
}
```

### `GET /api/v1/notes`
List all notes for a user.

**Query Parameters**:
- `user_id` (required): User identifier
- `topic` (optional): Filter by topic
- `limit` (optional, default: 30): Max results
- `offset` (optional, default: 0): Pagination offset

**Example**: `GET /api/v1/notes?user_id=user_123&topic=AI&limit=10`

**Response** (200):
```json
{
  "user_id": "user_123",
  "count": 2,
  "items": [
    {
      "id": "note-1",
      "title": "Introduction to Machine Learning",
      "description": "Basic concepts...",
      "tags": [{"type": "topic", "label": "AI"}],
      "created_at": "2026-02-04T16:30:00Z"
    }
  ]
}
```

### `GET /api/v1/notes/recent`
Get recent notes for dashboard.

**Query Parameters**:
- `user_id` (required)
- `limit` (optional, default: 6)

**Response**: Same format as list notes

### `GET /api/v1/notes/{note_id}`
Get a specific note.

**Query Parameters**:
- `user_id` (required)

**Response** (200): Single note object

### `PATCH /api/v1/notes/{note_id}`
Update a note.

**Query Parameters**:
- `user_id` (required)

**Request Body** (all fields optional):
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "tags": [{"type": "topic", "label": "Updated"}]
}
```

**Response** (200): Updated note object

---

## ⚙️ Settings API

### `GET /api/v1/settings/{user_id}`
Get user settings (DNA preferences).

**Response** (200):
```json
{
  "user_id": "user_123",
  "theme": "light",
  "notifications": {
    "in_app": true,
    "email": false,
    "push": false
  },
  "timezone": "America/Los_Angeles",
  "study_preferences": {
    "formats": ["audio", "notes", "video"],
    "preferences": ["quizzes", "analogies"],
    "custom_style": "I prefer detailed historical context",
    "cognitive_tone": "socratic"
  },
  "created_at": "2026-02-01T10:00:00Z",
  "updated_at": "2026-02-04T16:00:00Z"
}
```

### `PATCH /api/v1/settings/{user_id}`
Update user settings (upsert).

**Request Body** (all fields optional):
```json
{
  "theme": "dark",
  "notifications": {
    "in_app": true,
    "email": true
  },
  "study_preferences": {
    "formats": ["audio", "notes"],
    "preferences": ["quizzes", "knowledge_graph"],
    "cognitive_tone": "eli5",
    "custom_style": "Keep it simple and fun"
  }
}
```

**Response** (200): Updated settings object

---

## 📤 Upload API

### `POST /api/v1/upload`
Upload files for processing.

**Request**: `multipart/form-data`
- `user_id` (form field): User identifier
- `files` (file upload): One or more files

**Supported File Types**:
- PDF (.pdf)
- Text (.txt, .md)
- Audio (.mp3, .wav)
- Video (.mp4)

**Response** (200):
```json
{
  "user_id": "user_123",
  "uploaded": 2,
  "results": [
    {
      "filename": "lecture_notes.pdf",
      "status": "processing",
      "task_id": "task-uuid-789",
      "content_id": "content-uuid-101",
      "response": {
        "text": "Content ingested successfully"
      }
    },
    {
      "filename": "audio_lecture.mp3",
      "status": "processing",
      "task_id": "task-uuid-790",
      "content_id": "content-uuid-102"
    }
  ]
}
```

### `GET /api/v1/upload/status/{task_id}`
Check upload/ingestion status.

**Response** (200):
```json
{
  "task_id": "task-uuid-789",
  "status": "completed",
  "progress": 100,
  "result": {
    "content_id": "content-uuid-101",
    "topics": ["Machine Learning", "Neural Networks"]
  }
}
```

---

## 📚 Learning Plans API

### `POST /api/v1/learning-plans`
Create a learning plan.

**Request Body**:
```json
{
  "user_id": "user_123",
  "title": "Master Machine Learning Basics",
  "description": "4-week plan to learn ML fundamentals",
  "goal": "Prep for ML certification",
  "status": "proposed",
  "difficulty": "intermediate",
  "category": "AI & ML",
  "category_color": "#3B82F6",
  "estimated_time": "4 weeks",
  "weeks": 4,
  "sessions_per_week": 3,
  "items": [
    {
      "title": "Week 1: Introduction",
      "description": "Learn basic concepts",
      "status": "pending",
      "order_index": 0,
      "estimated_minutes": 120
    }
  ]
}
```

**Response** (201):
```json
{
  "plan": {
    "id": "plan-uuid-555",
    "user_id": "user_123",
    "title": "Master Machine Learning Basics",
    "status": "proposed",
    "created_at": "2026-02-04T16:30:00Z"
  },
  "items": [
    {
      "id": "item-uuid-666",
      "plan_id": "plan-uuid-555",
      "title": "Week 1: Introduction",
      "status": "pending",
      "order_index": 0
    }
  ]
}
```

### `GET /api/v1/learning-plans`
List learning plans.

**Query Parameters**:
- `user_id` (required)
- `status` (optional): Filter by status (proposed, active, paused, completed)
- `limit` (optional, default: 20)
- `offset` (optional, default: 0)

**Response** (200):
```json
{
  "user_id": "user_123",
  "count": 3,
  "items": [
    {
      "id": "plan-1",
      "title": "Master Machine Learning",
      "status": "active",
      "progress_percent": 45
    }
  ]
}
```

### `GET /api/v1/learning-plans/proposed`
Get proposed (recommended) plans.

**Query Parameters**:
- `user_id` (required)
- `limit` (optional, default: 10)

**Response**: Same format as list plans

### `GET /api/v1/learning-plans/{plan_id}`
Get a specific plan with items.

**Query Parameters**:
- `user_id` (required)
- `include_items` (optional, default: true)

**Response** (200):
```json
{
  "plan": {
    "id": "plan-1",
    "title": "Master ML",
    "status": "active"
  },
  "items": [
    {
      "id": "item-1",
      "title": "Week 1",
      "status": "done"
    }
  ]
}
```

### `PATCH /api/v1/learning-plans/{plan_id}`
Update a learning plan.

**Query Parameters**:
- `user_id` (required)

**Request Body** (all fields optional):
```json
{
  "title": "Updated Title",
  "status": "active",
  "progress_percent": 50
}
```

### `POST /api/v1/learning-plans/{plan_id}/approve`
Approve and activate a proposed plan.

**Query Parameters**:
- `user_id` (required)

**Response** (200): Updated plan with `status: "active"`

### `POST /api/v1/learning-plans/{plan_id}/pause`
Pause an active plan.

**Response** (200): Updated plan with `status: "paused"`

### `POST /api/v1/learning-plans/{plan_id}/resume`
Resume a paused plan.

**Response** (200): Updated plan with `status: "active"`

### `GET /api/v1/learning-plans/{plan_id}/progress`
Get plan progress statistics.

**Response** (200):
```json
{
  "plan_id": "plan-1",
  "total": 12,
  "completed": 5,
  "by_status": {
    "done": 5,
    "in_progress": 2,
    "pending": 5
  },
  "percent": 41.67
}
```

### `POST /api/v1/learning-plans/generate-suggested`
Generate AI-suggested learning plans.

**Query Parameters**:
- `user_id` (required)
- `context_mode` (optional, default: "growth"): Context for generation
- `max_plans` (optional, default: 3, max: 5): Number of plans to generate

**Response** (200):
```json
{
  "user_id": "user_123",
  "generated": 3,
  "plans": [
    {
      "id": "plan-new-1",
      "title": "Deep Learning Fundamentals",
      "status": "proposed",
      "difficulty": "intermediate",
      "weeks": 6
    }
  ]
}
```

---

## 🎨 Artifacts API

### `GET /api/v1/artifacts`
List generated artifacts (flashcards, summaries, etc.).

**Query Parameters**:
- `user_id` (required)
- `type` (optional): Filter by artifact type

**Response** (200):
```json
{
  "user_id": "user_123",
  "count": 5,
  "items": [
    {
      "id": "artifact-1",
      "artifact_type": "flashcards",
      "title": "ML Concepts Flashcards",
      "estimated_minutes": 15,
      "created_at": "2026-02-04T15:00:00Z",
      "content_ids": ["content-1", "content-2"]
    }
  ]
}
```

### `GET /api/v1/artifacts/{artifact_id}`
Get a specific artifact.

**Response** (200):
```json
{
  "id": "artifact-1",
  "artifact_type": "flashcards",
  "content": "Q: What is supervised learning?\nA: ...",
  "estimated_minutes": 15,
  "metadata": {
    "card_count": 20,
    "difficulty": "beginner"
  },
  "created_at": "2026-02-04T15:00:00Z"
}
```

---

## 🔄 Ingestion API

### `POST /api/v1/ingestion`
Create an ingestion job.

**Request Body**:
```json
{
  "user_id": "user_123",
  "name": "Process lecture PDF",
  "job_type": "pdf",
  "status": "ingesting",
  "progress": 0,
  "metadata": {
    "source": "upload",
    "task_id": "task-123",
    "content_id": "content-456"
  }
}
```

**Response** (201):
```json
{
  "id": "job-uuid-777",
  "user_id": "user_123",
  "name": "Process lecture PDF",
  "job_type": "pdf",
  "status": "ingesting",
  "progress": 0,
  "created_at": "2026-02-04T16:30:00Z"
}
```

### `GET /api/v1/ingestion/processing`
Get all processing jobs.

**Query Parameters**:
- `user_id` (required)

**Response** (200):
```json
{
  "user_id": "user_123",
  "count": 2,
  "items": [
    {
      "id": "job-1",
      "name": "Process lecture",
      "status": "ingesting",
      "progress": 45
    }
  ]
}
```

### `PATCH /api/v1/ingestion/{job_id}`
Update ingestion job status.

**Request Body**:
```json
{
  "status": "completed",
  "progress": 100
}
```

---

## 🔔 Notifications API

### `GET /api/v1/notifications`
List notifications.

**Query Parameters**:
- `user_id` (required)
- `unread_only` (optional, default: false)
- `limit` (optional, default: 20)

**Response** (200):
```json
{
  "user_id": "user_123",
  "count": 3,
  "items": [
    {
      "id": "notif-1",
      "channel": "in_app",
      "title": "Materials ready",
      "body": "Your study materials for 'ML Basics' are ready",
      "read_at": null,
      "created_at": "2026-02-04T16:25:00Z",
      "data": {
        "note_id": "note-123",
        "event": "created"
      }
    }
  ]
}
```

### `GET /api/v1/notifications/badge`
Get unread notification count.

**Query Parameters**:
- `user_id` (required)

**Response** (200):
```json
{
  "user_id": "user_123",
  "unread_count": 5
}
```

### `POST /api/v1/notifications/{notification_id}/read`
Mark notification as read.

**Query Parameters**:
- `user_id` (required)

**Response** (200):
```json
{
  "id": "notif-1",
  "read_at": "2026-02-04T16:30:00Z"
}
```

### `GET /api/v1/notifications/stream`
Server-sent events stream for real-time notifications.

**Query Parameters**:
- `user_id` (required)

**Response**: SSE stream
```
event: notification
data: {"id":"notif-1","title":"New material ready"}

event: ping
data: {"timestamp":"2026-02-04T16:30:00Z"}
```

---

## 💬 Chat API

### `POST /api/v1/chat`
Send a chat message and get AI response.

**Request Body**:
```json
{
  "user_id": "user_123",
  "message": "Explain supervised learning",
  "context": {
    "note_id": "note-456"
  }
}
```

**Response** (200):
```json
{
  "response": "Supervised learning is a type of machine learning where...",
  "sources": ["content-1", "content-2"]
}
```

---

## 🔍 Search API

### `GET /api/v1/search`
Search across notes, content, and materials.

**Query Parameters**:
- `user_id` (required)
- `q` (required): Search query
- `type` (optional): Filter by type (notes, content, artifacts)
- `limit` (optional, default: 20)

**Response** (200):
```json
{
  "query": "machine learning",
  "count": 15,
  "results": [
    {
      "type": "note",
      "id": "note-1",
      "title": "ML Introduction",
      "snippet": "...machine learning basics...",
      "relevance": 0.95
    }
  ]
}
```

---

## 📊 Dashboard API

### `GET /api/v1/dashboard`
Get dashboard summary data.

**Query Parameters**:
- `user_id` (required)

**Response** (200):
```json
{
  "user_id": "user_123",
  "stats": {
    "total_notes": 45,
    "active_plans": 2,
    "completed_sessions": 12
  },
  "recent_activity": [...]
}
```

---

## 📅 Calendar API

### `GET /api/v1/calendar/accounts`
List connected calendar accounts.

**Query Parameters**:
- `user_id` (required)

**Response** (200):
```json
{
  "accounts": [
    {
      "id": "acc-1",
      "provider": "google",
      "email": "user@gmail.com",
      "connected_at": "2026-02-01T10:00:00Z"
    }
  ]
}
```

### `GET /api/v1/calendar/google/auth-url`
Get Google OAuth URL.

**Query Parameters**:
- `user_id` (required)

**Response** (200):
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?..."
}
```

### `GET /api/v1/calendar/events`
List calendar events.

**Query Parameters**:
- `user_id` (required)
- `start_date` (optional): ISO date
- `end_date` (optional): ISO date

**Response** (200):
```json
{
  "events": [
    {
      "id": "event-1",
      "title": "Study Session: ML Basics",
      "start_time": "2026-02-05T14:00:00Z",
      "end_time": "2026-02-05T15:30:00Z",
      "calendar_id": "cal-1"
    }
  ]
}
```

### `POST /api/v1/calendar/events`
Create a calendar event.

**Request Body**:
```json
{
  "user_id": "user_123",
  "title": "Study Session",
  "start_time": "2026-02-05T14:00:00Z",
  "end_time": "2026-02-05T15:30:00Z",
  "calendar_id": "cal-1",
  "description": "Review ML concepts"
}
```

---

## Error Responses

All endpoints may return these error responses:

**400 Bad Request**:
```json
{
  "detail": "No fields to update"
}
```

**404 Not Found**:
```json
{
  "detail": "Note not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Database error"
}
```

**503 Service Unavailable**:
```json
{
  "detail": "Database connection unavailable"
}
```
