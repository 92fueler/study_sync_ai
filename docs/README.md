# StudySync AI - Documentation

> **Hackathon**: Gemini 3 Hackathon  
> **Team**: 2 Engineers + 1 PM  
> **Timeline**: 2 weeks

---

## Quick Links

| Document | Purpose | Audience |
|----------|---------|----------|
| [DESIGN.md](./DESIGN.md) | **System architecture, design principles, workflows** | Everyone |
| [impl-01-project-structure.md](./impl-01-project-structure.md) | Directory structure, file organization | Engineers |
| [impl-02-docker-infrastructure.md](./impl-02-docker-infrastructure.md) | Docker setup, ports, environment vars | Engineers |
| [impl-03-database-schema.md](./impl-03-database-schema.md) | Full SQL DDL, table relationships | Engineers |
| [impl-04-work-division.md](./impl-04-work-division.md) | Phases, work split, priorities | Everyone |
| [impl-05-verification.md](./impl-05-verification.md) | Health checks, test commands | Engineers |

---

## Document Structure

### High-Level Design (Start Here)

**[DESIGN.md](./DESIGN.md)** covers:
- Executive summary and value proposition
- Design principles (Proactive > Reactive, NEW vs RE-GEN philosophy)
- Architecture diagrams
- Agent responsibilities and A2A communication
- API contracts
- Workflow walkthroughs
- Multi-signal priority algorithm
- Key design decisions
- Open questions for team discussion

### Implementation Details

The `impl-*.md` files contain technical details for building the system:

1. **[Project Structure](./impl-01-project-structure.md)** - Where files go
2. **[Docker Infrastructure](./impl-02-docker-infrastructure.md)** - How to run it
3. **[Database Schema](./impl-03-database-schema.md)** - Data model
4. **[Work Division](./impl-04-work-division.md)** - Who builds what
5. **[Verification](./impl-05-verification.md)** - How to test it

---

## Architecture at a Glance

```
                    ┌─────────────────┐
                    │    Frontend     │
                    │  (Next.js:3000) │
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
                    │     Planner     │──────► Orchestrator :8005
                    │     :8004       │              │
                    └─────────────────┘              ▼
                                              ┌───────────┐
                                              │   Redis   │
                                              │   :6379   │
                                              └───────────┘
```

---

## Key Decisions Summary

| Decision | Choice |
|----------|--------|
| Agent communication | A2A Protocol (Google standard) |
| Content storage | Shared raw, personalized output |
| Background generation | Proactive for NEW, conservative for RE-GEN |
| Time variants | Calendar-aware + 5-min always available |
| Caching | Per (content_hash, profile_version) |
| Offline | PWA with 5-min summaries cached |

---

## Getting Started

### For Reviewers

1. Start with **[DESIGN.md](./DESIGN.md)** for the big picture
2. Check **[impl-04-work-division.md](./impl-04-work-division.md)** for phases and priorities
3. Review "Open Questions" section at the end of DESIGN.md

### For Engineers

1. Review **[DESIGN.md](./DESIGN.md)** for context
2. Set up environment per **[impl-02-docker-infrastructure.md](./impl-02-docker-infrastructure.md)**
3. Check your assigned work in **[impl-04-work-division.md](./impl-04-work-division.md)**
4. Use **[impl-05-verification.md](./impl-05-verification.md)** to test your work

---

## Open Questions for Team Review

1. **Cost Management**: Per-user Gemini API limits post-hackathon?
2. **Multi-tenant**: Organizations sharing content pools?
3. **Content Freshness**: "May be outdated" warnings for fast-moving domains?
4. **Learning Paths**: Multi-week curricula vs daily queues?
5. **Audio**: ElevenLabs vs Google TTS for podcast mode?

---

## Feedback Welcome

Please review and leave comments on:
- Architecture decisions
- Work division fairness
- Missing edge cases
- Demo flow ideas
