# Implementation: Project Structure

> **Document**: impl-01-project-structure.md  
> **Purpose**: Directory structure, file naming, module organization

---

## Directory Structure

```
study_sync_ai/
├── docs/                           # Design & implementation docs
│   ├── DESIGN.md
│   ├── impl-01-project-structure.md
│   ├── impl-02-docker-infrastructure.md
│   ├── impl-03-database-schema.md
│   ├── impl-04-work-division.md
│   ├── impl-05-verification.md
│   └── README.md
│
├── gateway/                        # FastAPI orchestrator
│   ├── app/
│   │   ├── main.py                # FastAPI app entry
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py      # API router aggregation
│   │   │       ├── upload.py      # POST /upload
│   │   │       ├── generate.py    # POST /generate
│   │   │       ├── chat.py        # POST /chat (SSE)
│   │   │       ├── content.py     # GET /content
│   │   │       ├── profile.py     # Profile CRUD
│   │   │       ├── artifacts.py   # Artifact retrieval
│   │   │       ├── queue.py       # Priority queue
│   │   │       ├── feedback.py    # Feedback submission
│   │   │       └── notifications.py
│   │   ├── a2a/
│   │   │   ├── __init__.py
│   │   │   └── client.py          # ADK runtime client (sessions + /run)
│   │   ├── db.py                  # Database helpers (asyncpg pool)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py          # Settings (env vars)
│   │   └── schemas/
│   │       └── __init__.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── agents/                         # ADK Agents (one per subdirectory)
│   ├── ingestion/
│   │   ├── agent.py               # ADK Agent definition
│   │   ├── tools.py               # ingest_content, extract_topics, etc.
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── profile/
│   │   ├── agent.py
│   │   ├── tools.py               # create_profile, get_calendar_context, etc.
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── synthesis/
│   │   ├── agent.py
│   │   ├── tools.py               # generate_note, create_5min_ver, etc.
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   ├── planner/
│   │   ├── agent.py
│   │   ├── tools.py               # prioritize, cluster, calc_effort, etc.
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── orchestrator/
│       ├── agent.py
│       ├── tools.py               # detect_changes, schedule_gen, etc.
│       ├── requirements.txt
│       └── Dockerfile
│
├── workers/                        # Background job workers
│   ├── generation_worker.py        # Calls Synthesis Agent
│   ├── notification_worker.py      # Sends notifications
│   ├── priority_worker.py          # Recalculates priority queue
│   ├── queue.py                    # RQ queue helpers
│   ├── jobs/                       # Job implementations
│   ├── requirements.txt
│   └── Dockerfile
│
├── supabase/                       # Database initialization
│   └── init.sql                   # Full schema DDL
│
├── scripts/                        # Dev + test scripts
├── tests/                          # Unit/integration tests
├── docker-compose.yml
├── .env.example
├── pytest.ini
└── README.md
```

---

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python modules | `snake_case.py` | `document_processor.py` |
| React components | `kebab-case.tsx` | `file-dropzone.tsx` |
| React hooks | `use-*.ts` | `use-generate-artifact.ts` |
| API routes | `snake_case.py` | `upload.py` |
| Config files | Standard names | `docker-compose.yml`, `package.json` |
| Agent cards | `agent_card.json` | Consistent across agents |

---

## Module Organization

### Frontend Modules (Not Implemented Yet)

The frontend is planned but not present in the current repo.

### Gateway Modules

```
gateway/app/
├── api/v1/        # HTTP endpoints (versioned)
├── a2a/           # ADK runtime client (sessions + /run)
├── core/          # Configuration, middleware
└── schemas/       # Pydantic models (TBD)
```

### Agent Modules

```
agents/{name}/
├── agent.py       # ADK Agent definition
└── tools.py       # Agent-specific tools
```

---

## Key Files Quick Reference

| Purpose | File Path |
|---------|-----------|
| Gateway entry | `gateway/app/main.py` |
| ADK runtime client | `gateway/app/a2a/client.py` |
| Upload endpoint | `gateway/app/api/v1/upload.py` |
| Generate endpoint | `gateway/app/api/v1/generate.py` |
| Synthesis agent | `agents/synthesis/agent.py` |
| Planner agent | `agents/planner/agent.py` |
| Orchestrator tools | `agents/orchestrator/tools.py` |
| Database schema | `supabase/init.sql` |
| Docker config | `docker-compose.yml` |
