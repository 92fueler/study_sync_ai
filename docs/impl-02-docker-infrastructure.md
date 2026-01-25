# Implementation: Docker Infrastructure

> **Document**: impl-02-docker-infrastructure.md  
> **Purpose**: Docker Compose configuration, service ports, network topology, environment variables

---

## Service Overview

| Service | Port | Image/Build | Purpose |
|---------|------|-------------|---------|
| frontend | 3000 | `./frontend` | Next.js UI |
| gateway | 8000 | `./gateway` | FastAPI orchestrator |
| ingestion-agent | 8001 | `./agents/ingestion` | File parsing |
| profile-agent | 8002 | `./agents/profile` | User modeling |
| synthesis-agent | 8003 | `./agents/synthesis` | Content generation |
| planner-agent | 8004 | `./agents/planner` | Prioritization |
| orchestrator-agent | 8005 | `./agents/orchestrator` | Background coordination |
| redis | 6379 | `redis:7-alpine` | Job queue |
| worker | - | `./workers` | Background jobs |
| supabase | 5432 | `supabase/postgres:15.1.0.117` | Database |

---

## Docker Compose Configuration

```yaml
version: '3.8'

services:
  # ============================================
  # FRONTEND
  # ============================================
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    depends_on:
      - gateway
    networks:
      - studysync

  # ============================================
  # GATEWAY (API Orchestrator)
  # ============================================
  gateway:
    build: ./gateway
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_URL=redis://redis:6379
      - INGESTION_AGENT_URL=http://ingestion-agent:8001
      - PROFILE_AGENT_URL=http://profile-agent:8002
      - SYNTHESIS_AGENT_URL=http://synthesis-agent:8003
      - PLANNER_AGENT_URL=http://planner-agent:8004
      - ORCHESTRATOR_AGENT_URL=http://orchestrator-agent:8005
    depends_on:
      - redis
      - supabase
    networks:
      - studysync

  # ============================================
  # ADK AGENTS
  # ============================================
  ingestion-agent:
    build: ./agents/ingestion
    ports:
      - "8001:8001"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
    networks:
      - studysync

  profile-agent:
    build: ./agents/profile
    ports:
      - "8002:8002"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    networks:
      - studysync

  synthesis-agent:
    build: ./agents/synthesis
    ports:
      - "8003:8003"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
    networks:
      - studysync

  planner-agent:
    build: ./agents/planner
    ports:
      - "8004:8004"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
    networks:
      - studysync

  orchestrator-agent:
    build: ./agents/orchestrator
    ports:
      - "8005:8005"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
      - REDIS_URL=redis://redis:6379
      - PROFILE_AGENT_URL=http://profile-agent:8002
      - SYNTHESIS_AGENT_URL=http://synthesis-agent:8003
      - PLANNER_AGENT_URL=http://planner-agent:8004
    depends_on:
      - redis
      - profile-agent
      - synthesis-agent
      - planner-agent
    networks:
      - studysync

  # ============================================
  # BACKGROUND WORKERS
  # ============================================
  worker:
    build: ./workers
    environment:
      - REDIS_URL=redis://redis:6379
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_SERVICE_KEY}
      - SYNTHESIS_AGENT_URL=http://synthesis-agent:8003
    depends_on:
      - redis
      - orchestrator-agent
    deploy:
      replicas: 2
    networks:
      - studysync

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
    image: supabase/postgres:15.1.0.117
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
│  │ Browser │────:3000───────────►│        frontend             │   │
│  └─────────┘                     │      (Next.js)              │   │
│                                  └──────────┬──────────────────┘   │
│                                             │                       │
│                                             ▼                       │
│                                  ┌─────────────────────────────┐   │
│  ┌─────────┐                     │        gateway              │   │
│  │API Test │────:8000───────────►│      (FastAPI)              │   │
│  └─────────┘                     │   A2A Orchestrator          │   │
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
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   │    redis     │     │    worker    │     │   supabase   │
│   │    :6379     │◄───►│   (×2)       │────►│    :5432     │
│   └──────────────┘     └──────────────┘     └──────────────┘
│                                                                      │
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
# SUPABASE
# ===========================================
SUPABASE_URL=http://localhost:5432
SUPABASE_ANON_KEY=your-anon-key
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
# CORS_ORIGINS=http://localhost:3000
```

---

## Dockerfile Templates

### Gateway Dockerfile

```dockerfile
# gateway/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY ../shared/ ./shared/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Agent Dockerfile (Template)

```dockerfile
# agents/{name}/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY agent_card.json .
COPY ../../shared/ ./shared/

EXPOSE 800X  # Replace X with agent port

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "800X"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

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

Each service exposes a health check:

| Service | Health Endpoint |
|---------|-----------------|
| Gateway | `GET http://localhost:8000/health` |
| Ingestion | `GET http://localhost:8001/health` |
| Profile | `GET http://localhost:8002/health` |
| Synthesis | `GET http://localhost:8003/health` |
| Planner | `GET http://localhost:8004/health` |
| Orchestrator | `GET http://localhost:8005/health` |

Agent cards are available at:
```
GET http://localhost:800X/.well-known/agent.json
```
