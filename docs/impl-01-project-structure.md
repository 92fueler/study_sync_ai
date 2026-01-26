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
├── frontend/                       # Next.js 14 (App Router)
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Landing/redirect
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── callback/page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx
│   │       ├── upload/page.tsx    # Main upload page
│   │       ├── queue/page.tsx     # Priority queue view
│   │       └── results/[id]/page.tsx  # Artifact viewer
│   ├── components/
│   │   ├── ui/                    # Shared UI (buttons, cards, etc.)
│   │   ├── upload/
│   │   │   ├── file-dropzone.tsx
│   │   │   ├── topic-input.tsx
│   │   │   ├── format-selector.tsx
│   │   │   └── style-selector.tsx
│   │   └── results/
│   │       ├── markdown-renderer.tsx
│   │       ├── mermaid-diagram.tsx
│   │       └── effort-badge.tsx
│   ├── hooks/
│   │   ├── use-supabase.ts
│   │   └── use-generate-artifact.ts
│   ├── lib/
│   │   ├── supabase/
│   │   │   ├── client.ts          # Browser client
│   │   │   └── server.ts          # Server client
│   │   ├── api.ts                 # FastAPI client
│   │   └── offline/
│   │       ├── cache-manager.ts   # IndexedDB wrapper
│   │       └── sync-queue.ts      # Offline action queue
│   ├── public/
│   │   ├── sw.js                  # Service worker for PWA
│   │   └── manifest.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── package.json
│   ├── Dockerfile
│   └── .env.local.example
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
│   │   │       ├── profile.py     # Profile CRUD
│   │   │       ├── artifacts.py   # Artifact retrieval
│   │   │       ├── queue.py       # Priority queue
│   │   │       ├── feedback.py    # Feedback submission
│   │   │       └── notifications.py
│   │   ├── a2a/
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # A2A task sender
│   │   │   └── discovery.py       # Agent card registry
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py          # Settings (env vars)
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── generate.py
│   │       ├── profile.py
│   │       └── artifacts.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── agents/                         # ADK Agents (one per subdirectory)
│   ├── ingestion/
│   │   ├── app/
│   │   │   ├── main.py            # FastAPI + A2A endpoints
│   │   │   ├── agent.py           # ADK Agent definition
│   │   │   └── tools.py           # parse_pdf, extract_topics, etc.
│   │   ├── agent_card.json
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── profile/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── agent.py
│   │   │   └── tools.py           # build_style_dna, get_gcal, etc.
│   │   ├── agent_card.json
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── synthesis/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── agent.py
│   │   │   └── tools.py           # generate_note, create_5min_ver, etc.
│   │   ├── agent_card.json
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── planner/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── agent.py
│   │   │   └── tools.py           # prioritize, cluster, calc_effort, etc.
│   │   ├── agent_card.json
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   └── orchestrator/
│       ├── app/
│       │   ├── main.py
│       │   ├── agent.py
│       │   └── tools.py           # detect_changes, schedule_gen, etc.
│       ├── agent_card.json
│       ├── requirements.txt
│       └── Dockerfile
│
├── workers/                        # Background job workers
│   ├── app/
│   │   ├── main.py                # Worker entry point
│   │   ├── generation_worker.py   # Calls Synthesis Agent
│   │   └── notification_worker.py # Sends notifications
│   ├── requirements.txt
│   └── Dockerfile
│
├── shared/                         # Shared Python utilities
│   ├── __init__.py
│   ├── a2a_protocol.py            # A2A message types
│   ├── gemini_client.py           # Shared Gemini 3 wrapper
│   └── supabase_client.py         # Shared Supabase client
│
├── supabase/                       # Database initialization
│   └── init.sql                   # Full schema DDL
│
├── docker-compose.yml
├── .env.example
├── .gitignore
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

### Frontend Modules

```
frontend/
├── app/           # Next.js App Router pages
├── components/    # Reusable UI components
│   ├── ui/        # Generic (buttons, cards, modals)
│   ├── upload/    # Upload-specific components
│   └── results/   # Result display components
├── hooks/         # Custom React hooks
└── lib/           # Utilities and clients
    ├── supabase/  # Supabase client setup
    └── offline/   # PWA/offline support
```

### Gateway Modules

```
gateway/app/
├── api/v1/        # HTTP endpoints (versioned)
├── a2a/           # A2A protocol handling
├── core/          # Configuration, middleware
└── schemas/       # Pydantic models
```

### Agent Modules

```
agents/{name}/app/
├── main.py        # FastAPI app with A2A endpoints
├── agent.py       # ADK Agent definition
└── tools.py       # Agent-specific tools
```

---

## Key Files Quick Reference

| Purpose | File Path |
|---------|-----------|
| Gateway entry | `gateway/app/main.py` |
| A2A client | `gateway/app/a2a/client.py` |
| Upload endpoint | `gateway/app/api/v1/upload.py` |
| Generate endpoint | `gateway/app/api/v1/generate.py` |
| Synthesis agent | `agents/synthesis/app/agent.py` |
| Planner agent | `agents/planner/app/agent.py` |
| File dropzone | `frontend/components/upload/file-dropzone.tsx` |
| Markdown renderer | `frontend/components/results/markdown-renderer.tsx` |
| Database schema | `supabase/init.sql` |
| Docker config | `docker-compose.yml` |
