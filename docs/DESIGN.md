# StudySync AI - System Design Document

> **Version**: 1.0  
> **Date**: January 25, 2026  
> **Status**: Ready for Team Review

---

## 1. Executive Summary

### Vision
An autonomous "Learning Partner" that transforms raw, messy inputs (links, voice memos, PDFs) into a pristine, personalized Knowledge Bank. The system proactively proposes structured learning plans, books conflict-free sessions on the user's calendar, and adapts content format (audio/text/quiz) to the user's daily context.

### Core Value Proposition
Save users time by:
1. **Intelligently prioritizing** what content matters most
2. **Generating personalized artifacts** that fit their available time

### Key Differentiators
- **Multi-signal content prioritization** (goals + trending + prerequisites + behavior)
- **Time-aware content generation** (calendar-aware + always-available 5-min option)
- **Full profile system** (Style DNA + explicit config + learning behavior)
- **Shared knowledge base** with personalized output per user
- **Proactive background generation** - content ready before user asks

---

## 2. Design Principles

### 2.1 Proactive > Reactive
The system should anticipate user needs rather than wait for explicit requests. When a user uploads content, the system immediately:
- Generates a 5-min summary
- Calculates priority score with reasoning
- Queues full artifact generation based on predicted needs

### 2.2 NEW Content = Proactive; RE-GEN = Conservative
**Critical distinction** in generation philosophy:

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| New content uploaded | Generate immediately | Reduce friction, save user time |
| Cluster detected | Propose study plan | Be helpful proactively |
| User requests regeneration | Prioritize highly | User action = pain point |
| Time passed | Do NOT auto-regenerate | Don't waste resources |
| Minor profile tweak | Do NOT regenerate | User didn't explicitly ask |

### 2.3 Personalization is P00
Every output should reflect the user's:
- Learning style (ELI5, Socratic, Academic)
- Format preferences (text, audio, visual)
- Time constraints (calendar-aware)
- Goals and domain interests

### 2.4 Shared Raw, Personal Output
- Raw content is stored once (deduped by hash)
- Each user gets uniquely generated artifacts from their profile
- Enables cross-user insights without duplicating storage

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              STUDYSYNC AI                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌──────────────────────────────────────────────────┐   │
│  │   Next.js   │     │           ADK Agent Orchestration Layer           │   │
│  │  Frontend   │◄───►│             (ADK Runtime /run_sse)                │   │
│  │  (Port 3000)│     │                                                   │   │
│  └─────────────┘     │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ │   │
│         │            │  │Ingestion │ │ Profile  │ │Synthesis │ │Planner│ │   │
│         │            │  │  Agent   │◄─►│  Agent   │◄─►│  Agent   │◄─►│Agent │ │   │
│         │            │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘ │   │
│         │            │       │            │            │          │      │   │
│         │            │       └────────────┴────────────┴──────────┘      │   │
│         │            │                         │                         │   │
│         │            │                ┌────────┴────────┐                │   │
│         │            │                │  Orchestrator   │                │   │
│         │            │                │     Agent       │                │   │
│         │            │                │ (Background)    │                │   │
│         │            │                └─────────────────┘                │   │
│         │            └──────────────────────────────────────────────────┘   │
│         │                                     │                              │
│         ▼                                     ▼                              │
│  ┌─────────────┐                    ┌─────────────────┐                     │
│  │  FastAPI    │◄──────────────────►│  Gemini 2.5     │                     │
│  │  Gateway    │                    │  Multimodal     │                     │
│  │ (Port 8000) │                    │  (Reasoning +   │                     │
│  └─────────────┘                    │   Vision +      │                     │
│         │                           │   Audio)        │                     │
│         ▼                           └─────────────────┘                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Data Layer                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │  Supabase   │  │  Supabase   │  │   pgvector  │  │   Google   │ │   │
│  │  │   Storage   │  │  PostgreSQL │  │ (Embeddings)│  │  Calendar  │ │   │
│  │  │ (Raw Files) │  │  (Profiles) │  │ (Clustering)│  │    API     │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  │                                                                      │   │
│  │  ┌─────────────┐                                                    │   │
│  │  │    Redis    │  (Job Queue + Signal Buffer)                       │   │
│  │  └─────────────┘                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Architecture (ADK Runtime)

### 4.1 Why ADK Runtime?
We currently use Google ADK's `api_server` runtime for inter-agent calls:
- **Working SoT**: Matches the ADK `api_server` session + `/run_sse` flow
- **Loose coupling**: Agents remain independently deployable
- **Future A2A**: We can add A2A JSON-RPC compatibility later if needed

### 4.2 Agent Network (ADK Runtime)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Agent Network                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────┐          ┌─────────────────────┐               │
│  │   INGESTION AGENT   │          │    PROFILE AGENT    │               │
│  ├─────────────────────┤          ├─────────────────────┤               │
│  │ Role: Content Parser│          │ Role: User Modeler  │               │
│  │                     │   ADK    │                     │               │
│  │ Tools:              │◄────────►│ Tools:              │               │
│  │ • parse_pdf()       │          │ • analyze_history() │               │
│  │ • parse_audio()     │          │ • build_style_dna() │               │
│  │ • parse_video()     │          │ • infer_goals()     │               │
│  │ • extract_topics()  │          │ • get_gcal_context()│               │
│  │ • generate_embed()  │          │ • ask_clarifying_q()│               │
│  └─────────┬───────────┘          └──────────┬──────────┘               │
│            │                                  │                          │
│            └──────────────┬───────────────────┘                          │
│                           │                                              │
│                           ▼                                              │
│  ┌─────────────────────┐          ┌─────────────────────┐               │
│  │  SYNTHESIS AGENT    │          │   PLANNER AGENT     │               │
│  ├─────────────────────┤          ├─────────────────────┤               │
│  │ Role: Content Gen   │   ADK    │ Role: Scheduler     │               │
│  │                     │◄────────►│                     │               │
│  │ Tools:              │          │ Tools:              │               │
│  │ • generate_note()   │          │ • cluster_topics()  │               │
│  │ • generate_script() │          │ • calc_effort()     │               │
│  │ • generate_quiz()   │          │ • find_time_slots() │               │
│  │ • apply_style()     │          │ • prioritize()      │               │
│  │ • create_5min_ver() │          │ • book_calendar()   │               │
│  └─────────────────────┘          └─────────────────────┘               │
│                                                                          │
│                    ┌─────────────────────────────┐                       │
│                    │    ORCHESTRATOR AGENT       │                       │
│                    ├─────────────────────────────┤                       │
│                    │ Role: Background Coordinator│                       │
│                    │                             │                       │
│                    │ Tools:                      │                       │
│                    │ • detect_material_changes() │                       │
│                    │ • analyze_user_signals()    │                       │
│                    │ • schedule_generation()     │                       │
│                    │ • predict_next_need()       │                       │
│                    │ • trigger_notification()    │                       │
│                    └─────────────────────────────┘                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Agent Responsibilities

| Agent | Role | Gemini Config | Key Tools |
|-------|------|---------------|-----------|
| **Ingestion** | Parse files, extract topics, generate embeddings | `thinking_level: low` (fast) | `parse_pdf`, `extract_topics`, `generate_embed` |
| **Profile** | Build user's Style DNA, read GCal, ask clarifying questions | `thinking_level: medium` | `build_style_dna`, `get_gcal_context`, `ask_clarifying_q` |
| **Synthesis** | Generate personalized artifacts with Gemini 2.5 | `thinking_level: high` (deep reasoning) | `generate_note`, `apply_style`, `create_5min_ver` |
| **Planner** | Multi-signal priority, clustering, effort estimation | `thinking_level: medium` | `prioritize`, `cluster_topics`, `calc_effort` |
| **Orchestrator** | Coordinate background generation | `thinking_level: medium` | `detect_material_changes`, `schedule_generation` |

### 4.4 ADK Runtime Call Flow

ADK `api_server` uses sessions and a `/run_sse` endpoint.

**Create session**:
```
POST /apps/{appName}/users/{userId}/sessions
```

**Run (SSE)** (request):
```json
{
  "app_name": "synthesis",
  "user_id": "user-123",
  "session_id": "task-uuid-here",
  "new_message": {
    "role": "user",
    "parts": [{"text": "{\"skill\": \"generate-5min\", \"content_id\": \"xxx\"}"}]
  }
}
```

**Run (SSE)** (response):
```json
[
  {"event": "thinking", "content": "..."},
  {"event": "final", "content": "Generated output here"}
]
```

---

## 5. API Contracts

### 5.1 Gateway API (External)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/upload` | Upload files, trigger ingestion |
| `POST` | `/api/v1/generate` | Generate artifact for user |
| `GET` | `/api/v1/artifacts/{id}` | Get specific artifact |
| `GET` | `/api/v1/queue` | Get prioritized content queue |
| `POST` | `/api/v1/profile` | Create/update user profile |
| `GET` | `/api/v1/profile/{user_id}` | Get user profile |
| `POST` | `/api/v1/feedback` | Submit artifact feedback |
| `GET` | `/api/v1/notifications` | Get user notifications |
| `GET` | `/api/v1/notifications/badge` | Get unread count |

### 5.2 Request/Response Schemas

**Generate Request**:
```typescript
interface GenerateRequest {
  user_id: string;
  content_ids?: string[];        // Specific content, or use queue
  time_available_minutes?: number; // Calendar-aware if not provided
  format?: "text" | "audio";
}
```

**Generate Response**:
```typescript
interface GenerateResponse {
  id: string;
  artifact_content: string;      // Markdown with Mermaid blocks
  artifact_5min?: string;        // Always-available quick version
  estimated_minutes: number;
  priority_score: number;
  priority_reasoning: string;    // "This is foundational for your goals..."
  format: string;
  created_at: string;
}
```

**Profile Schema**:
```typescript
interface UserProfile {
  user_id: string;
  display_name?: string;
  style_dna: {
    format_pref: "cornell" | "mindmap" | "outline";
    tone: "eli5" | "socratic" | "academic";
    uses_emoji: boolean;
    prefers_diagrams: boolean;
  };
  goals: string[];               // ["Learn Rust", "Master System Design"]
  calendar_context?: {
    commute_times: string[];     // ["8:00-8:30", "18:00-18:30"]
    work_hours: string;          // "9:00-17:00"
    timezone: string;
  };
}
```

### 5.3 Agent Runtime Endpoints (Internal)

Each agent (ADK `api_server`) exposes:
- `POST /apps/{appName}/users/{userId}/sessions` - Create session (returns session id)
- `POST /run_sse` - Execute with `app_name`, `user_id`, `session_id`, `new_message`

---

## 6. Workflow Walkthroughs

### 6.1 Content Upload & Prioritization Flow

```
┌──────┐  ┌────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐
│ User │  │Frontend│  │ Gateway │  │Ingestion│  │ Profile │  │Planner │
└──┬───┘  └───┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └───┬────┘
   │          │            │            │            │            │
   │ Upload   │            │            │            │            │
   │ 5 PDFs   │            │            │            │            │
   │─────────►│            │            │            │            │
   │          │            │            │            │            │
   │          │ POST /upload            │            │            │
   │          │───────────►│            │            │            │
   │          │            │            │            │            │
   │          │            │ ADK: /run_sse           │            │
   │          │            │───────────►│            │            │
   │          │            │            │            │            │
   │          │            │            │ Parse & Extract          │
   │          │            │            │ Topics + Embeddings      │
   │          │            │            │────────────────────────► │
   │          │            │            │            │            │
   │          │            │            │ ADK: Get User Profile    │
   │          │            │            │───────────►│            │
   │          │            │            │◄───────────│            │
   │          │            │            │ {goals, style_dna}      │
   │          │            │            │            │            │
   │          │            │            │ ADK: Calculate Priority  │
   │          │            │            │────────────────────────►│
   │          │            │            │            │ Multi-Signal│
   │          │            │            │            │ Ranking     │
   │          │            │            │◄────────────────────────│
   │          │            │            │ {priority_queue}        │
   │          │            │◄───────────│            │            │
   │          │◄───────────│            │            │            │
   │◄─────────│ "Here's what to study first..."     │            │
```

### 6.2 Time-Aware Content Generation Flow

```
┌──────┐  ┌────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ User │  │Frontend│  │ Gateway │  │ Profile │  │ Planner │  │Synthesis│
└──┬───┘  └───┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
   │          │            │            │            │             │
   │ "Generate│            │            │            │             │
   │  for me" │            │            │            │             │
   │─────────►│            │            │            │             │
   │          │            │            │            │             │
   │          │ POST /generate          │            │             │
   │          │───────────►│            │            │             │
   │          │            │            │            │             │
   │          │            │ ADK: Get calendar context             │
   │          │            │───────────►│            │             │
   │          │            │            │ Read GCal  │             │
   │          │            │            │ Find slot  │             │
   │          │            │◄───────────│            │             │
   │          │            │ {next_slot: 25min,      │             │
   │          │            │  context: "commute"}    │             │
   │          │            │            │            │             │
   │          │            │ ADK: Calculate effort   │             │
   │          │            │────────────────────────►│             │
   │          │            │◄────────────────────────│             │
   │          │            │ {fits_slot: true}       │             │
   │          │            │            │            │             │
   │          │            │ ADK: Generate with style│             │
   │          │            │─────────────────────────────────────►│
   │          │            │            │            │  Gemini 2.5 │
   │          │            │            │            │  + Style DNA│
   │          │            │◄─────────────────────────────────────│
   │          │◄───────────│            │            │             │
   │◄─────────│ Personalized 25min artifact          │             │
```

### 6.3 Background Generation Flow

```
┌────────────────┐
│  Orchestrator  │  (Runs continuously)
│    Agent       │
└───────┬────────┘
        │
        │ 1. Every 5 min: Check for changes
        │    - New uploads?
        │    - Behavior signals buffered?
        │    - Calendar slot approaching?
        ▼
┌───────────────┐      ┌───────────────┐
│    Profile    │◄────►│    Planner    │
│    Agent      │      │    Agent      │
└───────────────┘      └───────────────┘
        │                      │
        │ 2. Get user context  │ 3. Calculate what to generate
        │    + preferences     │    + priority
        ▼                      ▼
        └──────────┬───────────┘
                   │
                   │ 4. Enqueue generation job
                   │    (Redis queue with priority)
                   ▼
           ┌───────────────┐
           │   Synthesis   │
           │    Agent      │
           └───────┬───────┘
                   │
                   │ 5. Generate artifact
                   │    (5-min always, full if predicted)
                   ▼
           ┌───────────────┐
           │   Store in    │
           │   Supabase    │
           └───────┬───────┘
                   │
                   │ 6. Trigger notification
                   ▼
           ┌───────────────┐
           │  Notify User  │
           │ (push/in-app) │
           └───────────────┘
```

### 6.4 Behavior Signal Processing

**Immediate Triggers** (regenerate now):
- User updates goals in profile
- User changes style preferences
- User gives negative feedback (thumbs down)
- User explicitly requests "refresh"

**Batched Triggers** (wait, then process):
- User skips content (batch after 3+ skips)
- User reads partially (batch after pattern detected)
- Time-of-day preference shift (batch daily)
- Engagement pattern change (batch weekly)

---

## 7. Multi-Signal Priority Algorithm

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PRIORITY SCORE CALCULATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  For each content item:                                              │
│                                                                      │
│  ┌─────────────────┐                                                │
│  │  GOAL MATCH     │  weight: 0.40                                  │
│  │  Signal         │  • Semantic similarity to user's stated goals  │
│  │                 │  • Embedding cosine distance                    │
│  └────────┬────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │  TRENDING       │  weight: 0.25                                  │
│  │  Signal         │  • Recency of content                          │
│  │                 │  • Domain-specific trending (AI papers, etc.)  │
│  └────────┬────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │  PREREQUISITE   │  weight: 0.20                                  │
│  │  Signal         │  • Knowledge graph analysis                    │
│  │                 │  • "Learn X before Y" detection                │
│  └────────┬────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │  USER BEHAVIOR  │  weight: 0.15                                  │
│  │  Signal         │  • Past engagement with similar topics         │
│  │                 │  • Completion rates                            │
│  └────────┬────────┘                                                │
│           │                                                          │
│           ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  FINAL PRIORITY = Σ(signal_score × weight)                   │   │
│  │                                                               │   │
│  │  Output: Ranked queue with explanations                       │   │
│  │  "Study this first because it's foundational for your goals" │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8. Gemini 2.5 Integration

### 8.1 Model Configuration by Agent

| Agent | Model | Thinking Level | Special Features |
|-------|-------|----------------|------------------|
| Ingestion | `gemini-2.5-flash` | `low` | Vision (PDF/image parsing) |
| Profile | `gemini-2.5-flash` | `medium` | Conversation (clarifying Qs) |
| Synthesis | `gemini-2.5-flash` | `high` | Structured output, system instructions |
| Planner | `gemini-2.5-flash` | `medium` | Function calling |
| Orchestrator | `gemini-2.5-flash` | `medium` | Function calling |

**TODO**: Move to Gemini 3 family when generally available and stable.

### 8.2 Synthesis Agent Prompting

**TODO**: Move to Gemini 3 family when generally available and stable.

The Synthesis Agent receives the user's Style DNA as a system instruction:

```python
system_instruction = f"""
You are a synthesis agent creating study materials for a user with these preferences:
- Tone: {style_dna.tone}  # e.g., "eli5", "socratic", "academic"
- Format: {style_dna.format_pref}  # e.g., "cornell", "mindmap", "outline"
- Uses emojis: {style_dna.uses_emoji}
- Prefers diagrams: {style_dna.prefers_diagrams}

When creating content:
1. Match the requested tone exactly
2. Include Mermaid diagrams for complex concepts if prefers_diagrams is true
3. Generate a 5-minute condensed version alongside the full artifact
4. Estimate reading/study time based on content complexity
"""
```

---

## 9. High-Level Data Model

### 9.1 Core Entities

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  content_items  │     │  user_profiles  │     │    artifacts    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │     │ id              │
│ content_hash    │◄────│ user_id         │────►│ user_id         │
│ title           │     │ style_dna       │     │ content_ids[]   │
│ raw_text        │     │ goals[]         │     │ artifact_type   │
│ embedding       │     │ calendar_context│     │ content         │
│ topics          │     │ profile_version │     │ priority_score  │
│ media_type      │     └─────────────────┘     │ estimated_mins  │
└─────────────────┘                             └─────────────────┘
        │
        │ Links user to content
        ▼
┌─────────────────┐
│ user_materials  │
├─────────────────┤
│ user_id         │
│ content_id      │
│ status          │
└─────────────────┘
```

### 9.2 Background Processing Entities

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ background_jobs │     │behavior_signals │     │  notifications  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │     │ id              │
│ user_id         │     │ user_id         │     │ user_id         │
│ job_type        │     │ signal_type     │     │ channel         │
│ status          │     │ signal_data     │     │ title           │
│ priority        │     │ processed       │     │ body            │
│ payload         │     │ created_at      │     │ sent            │
│ created_at      │     └─────────────────┘     │ created_at      │
│ completed_at    │                             └─────────────────┘
│ error_message   │
└─────────────────┘
```

---

## 10. Notification System

### 10.1 Channels

| Channel | Trigger | Example |
|---------|---------|---------|
| **Push** | High-priority content ready | "Your React study guide is ready!" |
| **In-app badge** | Any new artifact | Badge count on Library tab |
| **Weekly email** | Sunday 9 AM | Digest of new content + recommendations |

### 10.2 Design Principle
- Push for important/actionable items only
- In-app for awareness without interruption
- Email for digest/summary (configurable)

---

## 11. Caching Strategy

### 11.1 Artifact Caching
Cache key: `(content_hash, profile_version, artifact_type)`

- Invalidate when profile changes (bump `profile_version`)
- 5-min summaries cached separately from full artifacts
- TTL: None (explicit invalidation only)

### 11.2 PWA Offline Support
Service Worker caches:
- All 5-min summaries (text) - Cache-first
- User's priority queue - Network-first
- Last 10 full artifacts - Network-first with fallback

---

## 12. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent runtime | ADK | Session + /run_sse flow (current SoT) |
| Content storage | Shared raw, personal output | Efficient storage, enables insights |
| Time variants | Calendar-aware + 5min always | Covers scheduled and impromptu |
| Auth | OAuth for GCal only | Simpler for hackathon |
| Background gen | Proactive for NEW, conservative for RE-GEN | Respect user intent |
| Caching | Per (content, profile_version) | Auto-invalidate on profile change |
| Feedback | Explicit + implicit | Comprehensive learning signal |
| Job retry | 3x with exponential backoff | Standard reliability |
| Offline | PWA with 5-min cached | True offline for quick access |

---

## 13. Open Questions for Team Discussion

1. **Cost Management**: Should we implement per-user Gemini API limits post-hackathon?
2. **Multi-tenant**: Could organizations share content pools? (e.g., company onboarding materials)
3. **Content Freshness**: For domains like AI where content ages fast, should we surface "this may be outdated"?
4. **Learning Paths**: Should the Planner Agent generate multi-week curricula, or just daily queues?
5. **Audio Generation**: TTS for podcast mode - ElevenLabs vs Google TTS?

---

## Related Documents
- [Implementation Plan](./impl-01-project-structure.md)
- [Docker Infrastructure](./impl-02-docker-infrastructure.md)
- [Database Schema](./impl-03-database-schema.md)
- [Work Division](./impl-04-work-division.md)
- [Verification Plan](./impl-05-verification.md)
