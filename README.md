# StudySync AI

An autonomous "Learning Partner" that automates the entire lifecycle of self-study. Transforms raw inputs (PDFs, text files, links) into personalized study materials using AI agents.

## 🚀 Quick Setup

**1. Environment Variables**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Required variables:
- `GEMINI_API_KEY` - Google Gemini API key
- `POSTGRES_PASSWORD` - PostgreSQL password (default: `postgres`)
- `SUPABASE_SERVICE_KEY` - Supabase service key (optional)

Frontend `.env` (auto-created if missing):
- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000/api/v1`)

**2. Start everything:**
```bash
./scripts/startup/start-fullstack-dev.sh
```

**3. Stop everything:**
```bash
./scripts/startup/stop-all.sh
```

**Manual start (separate terminals):**
```bash
docker-compose up -d redis supabase
docker-compose up -d profile-agent synthesis-agent ingestion-agent planner-agent orchestrator-agent
./scripts/startup/start-backend.sh    # Terminal 1
./scripts/startup/start-frontend.sh   # Terminal 2
```

## 📋 Prerequisites

- **Docker & Docker Compose** (for production and agents)
- **Node.js 24.x** (pinned version, use `nvm use` in frontend directory)
- **Python 3.10+** (for backend development)
- **tmux** (optional, for development convenience)

## 🏗️ Architecture

```
                    ┌─────────────────┐
                    │    Frontend     │
                    │  (React:3000)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Gateway     │
                    │ (FastAPI:8000)  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Ingestion   │  │    Profile    │  │   Synthesis   │
│    :8001      │  │    :8002      │  │    :8003      │
└───────────────┘  └───────────────┘  └───────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │     Planner    │──────► Orchestrator :8005
                    │     :8004      │              │
                    └────────────────┘              ▼
                                              ┌───────────┐
                                              │   Redis   │
                                              │   :6379   │
                                              └───────────┘
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | React + TypeScript UI |
| **Gateway** | 8000 | FastAPI backend orchestrator |
| **Ingestion Agent** | 8001 | Parses and stores uploaded content |
| **Profile Agent** | 8002 | Manages user profiles and preferences |
| **Synthesis Agent** | 8003 | Generates personalized study artifacts |
| **Planner Agent** | 8004 | Calculates content priority and study plans |
| **Orchestrator Agent** | 8005 | Coordinates background tasks |
| **Redis** | 6379 | Job queue and caching |
| **PostgreSQL** | 5432 | Database with pgvector |

## 📁 Project Structure

```
study_sync_ai/
├── frontend/          # React + TypeScript frontend
│   ├── src/
│   │   ├── api/      # API client and endpoints
│   │   ├── components/ # Reusable components
│   │   └── pages/     # Page components
│   └── package.json
├── gateway/           # FastAPI backend gateway
│   ├── app/
│   │   ├── api/v1/   # API endpoints
│   │   ├── a2a/      # ADK agent client
│   │   └── core/     # Configuration
│   └── requirements.txt
├── agents/            # ADK agents
│   ├── ingestion/     # Content parsing agent
│   ├── profile/       # User profile agent
│   ├── synthesis/     # Content generation agent
│   ├── planner/       # Priority calculation agent
│   └── orchestrator/  # Background coordination agent
├── workers/           # Background job workers
│   ├── generation_worker.py
│   ├── notification_worker.py
│   └── priority_worker.py
├── scripts/           # Startup and utility scripts
│   └── startup/       # Service startup scripts
├── docs/              # Detailed documentation
├── docker-compose.yml # Docker orchestration
└── .env               # Environment variables
```

## 🎯 Key Features

- **Proactive Generation**: Automatically creates 5-min summaries when content is uploaded
- **Personalization**: Adapts content to user's learning style (Style DNA)
- **Time-Aware**: Calendar-aware content generation
- **Priority Queue**: Intelligently ranks content based on goals, prerequisites, and behavior
- **Multi-Format**: Supports text, audio (podcast), and quiz formats
- **Learning DNA Onboarding**: Multi-step wizard to capture user preferences
- **Knowledge Bank**: Bulk file upload with drag & drop support
- **Study Session Viewer**: Split-screen interface with media player and Mermaid diagrams

## 🚦 Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📚 Documentation

| Document | Purpose |
|---------|---------|
| [USER_GUIDE.md](./USER_GUIDE.md) | Complete user guide with API endpoints and workflows |
| [docs/DESIGN.md](./docs/DESIGN.md) | System architecture and design principles |
| [docs/README.md](./docs/README.md) | Technical documentation index |
| [frontend/README.md](./frontend/README.md) | Frontend-specific documentation |
| [scripts/startup/README.md](./scripts/startup/README.md) | Startup scripts guide |

## 🧪 Testing

### Unit Tests

```bash
pytest tests/ --ignore=tests/test_integration.py -v
```

### Integration Tests

```bash
GEMINI_API_KEY=your-key pytest tests/test_integration.py -v
```

### E2E (Playwright)

```bash
npx --prefix frontend playwright install
npm --prefix frontend run test:e2e
```

See `docs/impl-05-verification.md` section 8.3 for full steps and expectations.

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # or :3000, :8001, etc.

# Kill the process
kill -9 <PID>
```

### Agents Not Running

```bash
# Check agent status
docker-compose ps

# Start missing agents
docker-compose up -d profile-agent synthesis-agent ingestion-agent planner-agent orchestrator-agent

# View logs
docker-compose logs -f profile-agent
```

### Frontend Dependencies Issues

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Backend Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r gateway/requirements.txt
```

## 🔗 API Endpoints

Key endpoints (see [USER_GUIDE.md](./USER_GUIDE.md) for complete list):

- `POST /api/v1/upload` - Upload files for processing
- `GET /api/v1/artifacts` - List user artifacts
- `GET /api/v1/artifacts/{id}` - Get specific artifact
- `POST /api/v1/profile` - Create user profile
- `GET /api/v1/profile/{user_id}` - Get user profile
- `GET /api/v1/notifications` - Get user notifications

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Web framework
- **ADK (Agent Development Kit)** - Agent runtime
- **PostgreSQL + pgvector** - Database with vector support
- **Redis** - Job queue and caching
- **Google Gemini API** - AI model

### Frontend
- **React 18** with TypeScript
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Mermaid.js** - Diagram rendering
- **Axios** - API client

