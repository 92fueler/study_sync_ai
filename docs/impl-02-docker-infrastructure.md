# Implementation: Docker Infrastructure

> **Document**: impl-02-docker-infrastructure.md  
> **Purpose**: Docker Compose configuration, service ports, network topology, environment variables

---

## Service Overview

| Service | Port | Image/Build | Purpose |
|---------|------|-------------|---------|
| gateway | 8000 | `gateway/Dockerfile` | FastAPI orchestrator |
| ingestion-agent | 8001 | `agents/ingestion/Dockerfile` | File parsing |
| profile-agent | 8002 | `agents/profile/Dockerfile` | User modeling |
| synthesis-agent | 8003 | `agents/synthesis/Dockerfile` | Content generation |
| planner-agent | 8004 | `agents/planner/Dockerfile` | Prioritization |
| orchestrator-agent | 8005 | `agents/orchestrator/Dockerfile` | Background coordination |
| generation-worker | - | `workers/Dockerfile` | Generate artifacts |
| notification-worker | - | `workers/Dockerfile` | Send notifications |
| priority-worker | - | `workers/Dockerfile` | Recalculate priority |
| redis | 6379 | `redis:7-alpine` | Job queue |
| supabase | 5432 | `pgvector/pgvector:pg15` | Database |

---

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  # ============================================
  # GATEWAY (API Orchestrator)
  # ============================================
  gateway:
    build:
      context: .
      dockerfile: gateway/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@supabase:5432/studysync
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_URL=redis://redis:6379
      - INGESTION_AGENT_URL=http://ingestion-agent:8001
      - PROFILE_AGENT_URL=http://profile-agent:8002
      - SYNTHESIS_AGENT_URL=http://synthesis-agent:8003
      - PLANNER_AGENT_URL=http://planner-agent:8004
      - ORCHESTRATOR_AGENT_URL=http://orchestrator-agent:8005
    depends_on:
      supabase:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - studysync

  # ============================================
  # ADK AGENTS
  # ============================================
  ingestion-agent:
    build:
      context: .
      dockerfile: agents/ingestion/Dockerfile
    ports:
      - "8001:8001"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@supabase:5432/studysync
    networks:
      - studysync

  profile-agent:
    build:
      context: .
      dockerfile: agents/profile/Dockerfile
    ports:
      - "8002:8002"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@supabase:5432/studysync
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    networks:
      - studysync

  synthesis-agent:
    build:
      context: .
      dockerfile: agents/synthesis/Dockerfile
    ports:
      - "8003:8003"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@supabase:5432/studysync
    networks:
      - studysync

  planner-agent:
    build:
      context: .
      dockerfile: agents/planner/Dockerfile
    ports:
      - "8004:8004"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@supabase:5432/studysync
    networks:
      - studysync

  orchestrator-agent:
    build:
      context: .
      dockerfile: agents/orchestrator/Dockerfile
    ports:
      - "8005:8005"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD:-postgres}@supabase:5432/studysync
      - REDIS_URL=redis://redis:6379
    depends_on:
      supabase:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - studysync

  # ============================================
  # WORKERS (RQ-based background job processing)
  # ============================================
  generation-worker:
    build:
      context: .
      dockerfile: workers/Dockerfile
    command: python -m workers.generation_worker
    environment:
      - REDIS_URL=redis://redis:6379
      - SYNTHESIS_AGENT_URL=http://synthesis-agent:8003
      - PROFILE_AGENT_URL=http://profile-agent:8002
      - ORCHESTRATOR_AGENT_URL=http://orchestrator-agent:8005
    depends_on:
      - redis
      - synthesis-agent
      - profile-agent
    networks:
      - studysync
    restart: unless-stopped

  notification-worker:
    build:
      context: .
      dockerfile: workers/Dockerfile
    command: python -m workers.notification_worker
    environment:
      - REDIS_URL=redis://redis:6379
      - ORCHESTRATOR_AGENT_URL=http://orchestrator-agent:8005
    depends_on:
      - redis
      - orchestrator-agent
    networks:
      - studysync
    restart: unless-stopped

  priority-worker:
    build:
      context: .
      dockerfile: workers/Dockerfile
    command: python -m workers.priority_worker
    environment:
      - REDIS_URL=redis://redis:6379
      - PLANNER_AGENT_URL=http://planner-agent:8004
    depends_on:
      - redis
      - planner-agent
    networks:
      - studysync
    restart: unless-stopped

  # ============================================
  # INFRASTRUCTURE
  # ============================================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - studysync

  supabase:
    image: pgvector/pgvector:pg15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}
      - POSTGRES_DB=studysync
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./supabase/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - studysync
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

# ============================================
# NETWORKS & VOLUMES
# ============================================
networks:
  studysync:
    driver: bridge

volumes:
  redis_data:
  postgres_data:
```

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DOCKER NETWORK: studysync                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    External                         Internal Network                 │
│    ────────                         ────────────────                 │
│                                                                      │
│  ┌─────────┐                     ┌─────────────────────────────┐   │
│  │API Test │────:8000───────────►│        gateway              │   │
│  └─────────┘                     │      (FastAPI)             │   │
│                                  └──────────┬──────────────────┘   │
│                                             │                       │
│              ┌──────────────────────────────┼──────────────────────┐
│              │                              │                      │
│              ▼                              ▼                      ▼
│   ┌──────────────┐             ┌──────────────┐          ┌──────────────┐
│   │  ingestion   │             │   profile    │          │  synthesis   │
│   │    :8001     │             │    :8002     │          │    :8003     │
│   └──────────────┘             └──────────────┘          └──────────────┘
│              │                              │                      │
│              └──────────────────────────────┼──────────────────────┘
│                                             │
│                              ┌──────────────┴──────────────┐
│                              ▼                              ▼
│                   ┌──────────────┐              ┌──────────────┐
│                   │   planner    │              │ orchestrator │
│                   │    :8004     │              │    :8005     │
│                   └──────────────┘              └──────┬───────┘
│                                                        │
│              ┌─────────────────────────────────────────┘
│              │
│              ▼
│   ┌──────────────┐     ┌──────────────────────┐     ┌──────────────┐
│   │    redis     │     │      workers         │     │   supabase   │
│   │    :6379     │◄───►│ generation/notify/   │────►│    :5432     │
│   └──────────────┘     │ priority (no ports)  │     └──────────────┘
│                        └──────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Environment Variables

### Required `.env` File

```bash
# ===========================================
# GEMINI API
# ===========================================
GEMINI_API_KEY=your-gemini-api-key

# ===========================================
# DATABASE / SUPABASE (Postgres)
# ===========================================
# Used by asyncpg (direct Postgres URL)
SUPABASE_URL=postgresql://postgres:postgres@localhost:5432/studysync
SUPABASE_SERVICE_KEY=your-service-key

# ===========================================
# GOOGLE OAUTH (for Calendar)
# ===========================================
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# ===========================================
# DATABASE
# ===========================================
POSTGRES_PASSWORD=postgres

# ===========================================
# OPTIONAL OVERRIDES
# ===========================================
# REDIS_URL=redis://redis:6379
```

---

## Dockerfile Templates

### Gateway Dockerfile

```dockerfile
# gateway/Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gateway/app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Agent Dockerfile (Template)

```dockerfile
# agents/{name}/Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY agents/{name}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/{name}/ ./{name}/

EXPOSE 800X  # Replace X with agent port

ENV PYTHONPATH=/app

CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "800X", "."]
```

### Frontend Dockerfile

Not implemented yet.

---

## Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f gateway
docker-compose logs -f synthesis-agent

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose build synthesis-agent
docker-compose up -d synthesis-agent

# Scale workers
docker-compose up -d --scale worker=4

# Reset database
docker-compose down -v
docker-compose up -d
```

---

## Health Check Endpoints

Only the gateway exposes a health endpoint by default:

| Service | Health Endpoint |
|---------|-----------------|
| Gateway | `GET http://localhost:8000/health` |

ADK agents may not expose `/health` (404 is expected).
