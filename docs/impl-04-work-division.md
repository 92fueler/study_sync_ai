# Implementation: Work Division

> **Document**: impl-04-work-division.md  
> **Purpose**: Development phases, work split between engineers, feature priorities

---

## Team Structure

- **2 Engineers** + 1 PM
- **Timeline**: 2 weeks (limited bandwidth)
- **Approach**: Mob on scaffolding first, then split by pipeline

---

## Phase 1: Agent Scaffolding (Mob Together)

**Duration**: Days 1-2  
**Goal**: Get all 5 ADK agents running with A2A communication before adding features.

### Checklist

- [ ] Set up repository structure (see `impl-01-project-structure.md`)
- [ ] Create `docker-compose.yml` with all services
- [ ] Create base ADK agent template
- [ ] Create Agent Cards for all 5 agents
- [ ] Implement A2A client in gateway
- [ ] Implement A2A endpoints in each agent
- [ ] Verify agents can communicate (ping-pong test)
- [ ] Set up Supabase schema (run `init.sql`)
- [ ] Configure environment variables

### Deliverables

1. `docker-compose up` starts all services
2. Each agent responds at `/.well-known/agent.json`
3. Gateway can send A2A task to any agent and get response
4. Database tables exist and are accessible

---

## Phase 2: Feature Implementation (Split Work)

**Duration**: Days 3-8  
**Goal**: Build core features in parallel pipelines.

### Engineer A: Input Pipeline

**Ownership**: Upload → Ingestion → Profile

| File | Description |
|------|-------------|
| `frontend/components/upload/file-dropzone.tsx` | Drag & drop file upload |
| `frontend/app/(dashboard)/upload/page.tsx` | Upload page |
| `gateway/app/api/v1/upload.py` | Upload endpoint |
| `agents/ingestion/app/tools.py` | `parse_pdf`, `extract_topics`, `generate_embed` |
| `agents/profile/app/tools.py` | `build_style_dna`, `get_gcal_context` |

**Flow to implement**:
1. User drops files in dropzone
2. Frontend uploads to Supabase Storage
3. Frontend calls `POST /api/v1/upload`
4. Gateway sends A2A task to Ingestion Agent
5. Ingestion extracts text, topics, embeddings
6. Gateway sends A2A task to Profile Agent
7. Profile returns user context
8. Gateway stores processed data

### Engineer B: Output Pipeline

**Ownership**: Planner → Synthesis → Display

| File | Description |
|------|-------------|
| `frontend/components/results/markdown-renderer.tsx` | Markdown + Mermaid display |
| `frontend/components/results/effort-badge.tsx` | Time estimate badge |
| `frontend/app/(dashboard)/results/[id]/page.tsx` | Results page |
| `gateway/app/api/v1/generate.py` | Generate endpoint |
| `agents/planner/app/tools.py` | `prioritize`, `cluster_topics`, `calc_effort` |
| `agents/synthesis/app/tools.py` | `generate_note`, `apply_style`, `create_5min_ver` |

**Flow to implement**:
1. User clicks "Generate" or system triggers
2. Frontend calls `POST /api/v1/generate`
3. Gateway sends A2A task to Profile Agent (get context)
4. Gateway sends A2A task to Planner Agent (calc priority)
5. Gateway sends A2A task to Synthesis Agent (generate)
6. Synthesis returns artifact + 5-min version
7. Gateway stores and returns artifact
8. Frontend renders with Mermaid diagrams

---

## Phase 3: Integration & Polish

**Duration**: Days 6-10  
**Goal**: Wire up full pipeline, add polish.

### Joint Work

- [ ] Wire upload pipeline to generation pipeline
- [ ] Implement priority queue endpoint (`GET /api/v1/queue`)
- [ ] Add feedback collection (`POST /api/v1/feedback`)
- [ ] Implement artifact caching (check before regenerate)
- [ ] Add loading states and error handling
- [ ] Basic UI styling

### Background Generation (Split)

**Engineer A**:
- [ ] Orchestrator Agent: `detect_material_changes`
- [ ] Worker: Generation job processing
- [ ] Redis job queue integration

**Engineer B**:
- [ ] Orchestrator Agent: `schedule_generation`
- [ ] Notification system (in-app badge)
- [ ] PWA service worker setup

---

## Phase 4: Demo Prep

**Duration**: Days 11-14  
**Goal**: End-to-end testing, bug fixes, demo polish.

### Checklist

- [ ] End-to-end flow testing
- [ ] Bug fixes
- [ ] Edge case handling
- [ ] Prepare demo script
- [ ] Record backup video (in case of live demo issues)
- [ ] Rehearse demo

---

## Feature Priority Matrix

### P0: Must Have for Demo

| Feature | Owner | Agent/Component |
|---------|-------|-----------------|
| File upload (PDF, TXT, MD) | Eng A | Ingestion |
| Content extraction | Eng A | Ingestion |
| Topic & embedding generation | Eng A | Ingestion |
| User profile with Style DNA | Eng A | Profile |
| Multi-signal priority scoring | Eng B | Planner |
| Time-aware artifact generation | Eng B | Synthesis |
| 5-minute quick version (always) | Eng B | Synthesis |
| Markdown + Mermaid rendering | Eng B | Frontend |
| Priority queue view | Either | Frontend |

### P1: Nice to Have

| Feature | Owner | Agent/Component |
|---------|-------|-----------------|
| Google Calendar integration | Eng A | Profile |
| Background generation | Both | Orchestrator |
| Explicit thumbs up/down | Eng B | Frontend |
| Implicit engagement tracking | Eng B | Planner |
| Artifact caching | Either | Gateway |
| In-app notifications | Eng B | Frontend |

### P2: Stretch Goals

| Feature | Owner | Agent/Component |
|---------|-------|-----------------|
| Audio generation (TTS) | Eng B | Synthesis |
| PWA offline support | Eng B | Frontend |
| Weekly email digest | Either | Worker |
| Calendar event booking | Eng A | Planner |

---

## Daily Sync Points

| Day | Focus | Sync Topic |
|-----|-------|------------|
| 1-2 | Scaffolding | "Can all agents talk to each other?" |
| 3 | Start split | "Interface contracts clear?" |
| 5 | Mid-split | "Any blockers? Need help?" |
| 7 | Integration | "Pipelines connecting?" |
| 10 | Polish | "What's left for demo?" |
| 12 | Testing | "Found any bugs?" |
| 14 | Demo | "Ready to present!" |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| A2A complexity | Can collapse to 2 agents (Ingestion+Profile, Synthesis+Planner) |
| Gemini API limits | Monitor usage, implement caching early |
| Time crunch | P0 features only, skip P1/P2 |
| Live demo fails | Pre-recorded backup video |

---

## Success Criteria

### Hackathon Demo Must Show

1. **Upload Flow**: Drop a PDF, see it processed
2. **Personalization**: Same content, different style outputs
3. **Priority**: "Here's why this is #1 on your list"
4. **Time-Aware**: "You have 25 minutes, here's a 25-min version"
5. **5-Min Always**: Quick version available instantly
6. **Agent Architecture**: Mention A2A, show agent cards

### "Wow" Moments to Aim For

1. Upload 5 PDFs, get instant priority ranking with reasoning
2. Show same content rendered ELI5 vs Academic
3. "I detected you have a 30-min commute, here's an audio version"
4. Mermaid diagram auto-generated for complex concept
