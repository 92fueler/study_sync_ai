# Implementation: Database Schema

> **Document**: impl-03-database-schema.md  
> **Purpose**: Full SQL DDL for Supabase, table relationships, indexes, RLS policies

---

## Overview

The database uses PostgreSQL (via Supabase) with the following extensions:
- `uuid-ossp` - UUID generation
- `vector` - pgvector for embeddings

---

## Full Schema DDL

```sql
-- ===========================================
-- EXTENSIONS
-- ===========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ===========================================
-- 1. CONTENT ITEMS (Shared across users)
-- ===========================================
-- Raw content is stored once and linked to users via user_materials
CREATE TABLE content_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  content_hash TEXT UNIQUE NOT NULL,  -- SHA256 hash for deduplication
  title TEXT,
  raw_text TEXT,
  media_type TEXT CHECK (media_type IN ('PDF', 'TXT', 'MARKDOWN', 'AUDIO', 'VIDEO', 'URL')),
  embedding vector(3072),             -- Gemini embedding dimension
  topics JSONB,                       -- Extracted topics: ["React", "Hooks", "State"]
  word_count INT,                     -- For effort estimation
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for vector similarity search (clustering)
-- NOTE: pgvector limits indexed dims to 2000 for vector, so we cast to halfvec.
CREATE INDEX idx_content_embedding ON content_items 
  USING hnsw ((embedding::halfvec(3072)) halfvec_cosine_ops);

-- Query note: use the same cast to leverage the index, e.g.
-- ORDER BY (embedding::halfvec(3072)) <=> '[...]'

-- Index for deduplication lookup
CREATE INDEX idx_content_hash ON content_items(content_hash);

-- ===========================================
-- 2. USER MATERIALS (Links users to content)
-- ===========================================
CREATE TABLE user_materials (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,              -- User identifier (no foreign key for demo)
  content_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
  storage_path TEXT,                  -- Supabase Storage path to original file
  status TEXT DEFAULT 'UNPROCESSED' CHECK (status IN (
    'UNPROCESSED', 'PROCESSING', 'PROCESSED', 'FAILED', 'ARCHIVED'
  )),
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_materials_user ON user_materials(user_id);
CREATE INDEX idx_user_materials_status ON user_materials(status);

-- ===========================================
-- 3. USER PROFILES (Style DNA + Preferences)
-- ===========================================
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT UNIQUE NOT NULL,
  display_name TEXT,
  
  -- Style DNA (how to format output)
  style_dna JSONB DEFAULT '{
    "format_pref": "outline",
    "tone": "eli5",
    "uses_emoji": false,
    "prefers_diagrams": true
  }'::jsonb,
  
  -- Learning goals
  goals JSONB DEFAULT '[]'::jsonb,    -- ["Learn Rust", "Master System Design"]
  
  -- Calendar context (from GCal)
  calendar_context JSONB,             -- {"commute_times": ["8:00-8:30"], "work_hours": "9-17"}
  
  -- Profile versioning (for cache invalidation)
  profile_version INT DEFAULT 1,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_profiles_user ON user_profiles(user_id);

-- ===========================================
-- 4. ARTIFACTS (Generated content, cached)
-- ===========================================
CREATE TABLE artifacts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  
  -- Source content (array of content_item IDs)
  content_ids UUID[] NOT NULL,
  
  -- Cache key components
  profile_version INT NOT NULL,       -- Invalidate when profile changes
  
  -- Artifact details
  artifact_type TEXT NOT NULL CHECK (artifact_type IN ('full', '5min', 'podcast', 'quiz')),
  format TEXT DEFAULT 'text' CHECK (format IN ('text', 'audio')),
  
  -- Generated content
  content TEXT NOT NULL,              -- Markdown with Mermaid blocks
  
  -- Metadata
  estimated_minutes INT,
  priority_score FLOAT,
  priority_reasoning TEXT,            -- "This is foundational for your goals..."
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_artifacts_user ON artifacts(user_id);
CREATE INDEX idx_artifacts_cache ON artifacts(user_id, content_ids, profile_version, artifact_type);

-- ===========================================
-- 5. FEEDBACK (Learning signal)
-- ===========================================
CREATE TABLE feedback (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  artifact_id UUID REFERENCES artifacts(id) ON DELETE CASCADE,
  
  -- Explicit feedback
  explicit_rating INT CHECK (explicit_rating BETWEEN 1 AND 5),  -- 1-5 stars or thumbs
  
  -- Implicit feedback
  time_spent_seconds INT,
  scroll_depth_percent INT,           -- How far they scrolled
  completed BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_feedback_user ON feedback(user_id);
CREATE INDEX idx_feedback_artifact ON feedback(artifact_id);

-- ===========================================
-- 6. BACKGROUND JOBS (Job queue tracking)
-- ===========================================
CREATE TABLE background_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  
  job_type TEXT NOT NULL CHECK (job_type IN (
    'generate_5min_new',      -- Generate 5-min summary for new content
    'generate_full_new',      -- Generate full artifact (predicted need)
    'regenerate_existing',    -- User-requested regeneration
    'recalc_priority',        -- Recalculate priority queue
    'send_notification'       -- Send notification
  )),
  
  status TEXT DEFAULT 'QUEUED' CHECK (status IN (
    'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'
  )),
  
  priority TEXT DEFAULT 'NORMAL' CHECK (priority IN ('HIGH', 'NORMAL', 'LOW')),
  
  -- Job payload (content_ids, etc.)
  payload JSONB,
  
  -- Retry tracking
  attempts INT DEFAULT 0,
  max_attempts INT DEFAULT 3,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  
  -- Error tracking
  error_message TEXT
);

CREATE INDEX idx_jobs_status ON background_jobs(status, priority, created_at);
CREATE INDEX idx_jobs_user ON background_jobs(user_id);

-- ===========================================
-- 7. BEHAVIOR SIGNALS (Buffered for batching)
-- ===========================================
CREATE TABLE behavior_signals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  
  signal_type TEXT NOT NULL CHECK (signal_type IN (
    'skip',           -- User skipped content
    'partial_read',   -- User read < 50%
    'complete',       -- User completed content
    'feedback',       -- User gave feedback
    'goal_change',    -- User modified goals
    'style_change'    -- User modified style preferences
  )),
  
  signal_data JSONB,                  -- Additional context
  processed BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_signals_unprocessed ON behavior_signals(user_id, processed) 
  WHERE NOT processed;

-- ===========================================
-- 8. NOTIFICATIONS
-- ===========================================
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  
  channel TEXT NOT NULL CHECK (channel IN ('push', 'in_app', 'email')),
  
  title TEXT,
  body TEXT,
  data JSONB,                         -- Artifact ID, deep link, etc.
  
  sent BOOLEAN DEFAULT FALSE,
  read BOOLEAN DEFAULT FALSE,
  
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, read);
CREATE INDEX idx_notifications_unsent ON notifications(sent) WHERE NOT sent;

-- ===========================================
-- 9. LEARNING PLANS
-- ===========================================
CREATE TABLE learning_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  title TEXT,
  description TEXT,
  goal TEXT,
  status TEXT DEFAULT 'proposed' CHECK (status IN ('proposed', 'active', 'paused', 'completed', 'archived')),
  difficulty TEXT,
  category TEXT,
  category_color TEXT,
  estimated_time TEXT,
  module_count INT,
  progress_percent INT DEFAULT 0,
  total_modules INT,
  completed_modules INT,
  next_session_at TIMESTAMPTZ,
  paused_at TIMESTAMPTZ,
  weeks INT,
  sessions_per_week INT,
  details JSONB,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_plans_user ON learning_plans(user_id);
CREATE INDEX idx_learning_plans_status ON learning_plans(user_id, status);

CREATE TABLE learning_plan_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  plan_id UUID REFERENCES learning_plans(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  content_ids UUID[],
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'done', 'skipped')),
  order_index INT DEFAULT 0,
  estimated_minutes INT,
  scheduled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_plan_items_plan ON learning_plan_items(plan_id);
CREATE INDEX idx_learning_plan_items_user ON learning_plan_items(user_id);

-- ===========================================
-- 10. LEARNING NOTES
-- ===========================================
CREATE TABLE learning_notes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  note_type TEXT NOT NULL CHECK (note_type IN ('pdf', 'video', 'audio', 'image', 'url', 'text')),
  title TEXT NOT NULL,
  description TEXT,
  tags JSONB,
  author TEXT,
  topic TEXT,
  thumbnail_url TEXT,
  source_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learning_notes_user ON learning_notes(user_id);
CREATE INDEX idx_learning_notes_topic ON learning_notes(user_id, topic);

-- ===========================================
-- 11. INGESTION JOBS
-- ===========================================
CREATE TABLE ingestion_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  name TEXT NOT NULL,
  job_type TEXT NOT NULL CHECK (job_type IN ('pdf', 'video', 'audio', 'image', 'url', 'text')),
  status TEXT NOT NULL CHECK (status IN ('ingesting', 'style-matching', 'ready', 'failed')),
  progress INT DEFAULT 0,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ingestion_jobs_user ON ingestion_jobs(user_id, status);

-- ===========================================
-- 12. USER SETTINGS
-- ===========================================
CREATE TABLE user_settings (
  user_id TEXT PRIMARY KEY,
  theme TEXT DEFAULT 'light',
  notifications JSONB DEFAULT '{
    "in_app": true,
    "email": false,
    "push": false
  }'::jsonb,
  timezone TEXT,
  study_preferences JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ===========================================
-- 13. CALENDAR INTEGRATIONS (LOCAL-FIRST)
-- ===========================================
CREATE TABLE calendar_accounts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  provider TEXT NOT NULL CHECK (provider IN ('local', 'google', 'microsoft', 'apple')),
  email TEXT,
  status TEXT DEFAULT 'disconnected' CHECK (status IN ('connected', 'disconnected')),
  auth_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calendar_accounts_user ON calendar_accounts(user_id);

CREATE TABLE calendar_calendars (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  provider TEXT NOT NULL CHECK (provider IN ('local', 'google', 'microsoft', 'apple')),
  external_id TEXT,
  name TEXT NOT NULL,
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calendar_calendars_user ON calendar_calendars(user_id);

CREATE TABLE calendar_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'local' CHECK (provider IN ('local', 'google', 'microsoft', 'apple')),
  calendar_id UUID REFERENCES calendar_calendars(id) ON DELETE SET NULL,
  external_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calendar_events_user ON calendar_events(user_id, start_time);

-- ===========================================
-- ROW LEVEL SECURITY (RLS)
-- ===========================================
ALTER TABLE user_materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE background_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE behavior_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_plan_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingestion_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_calendars ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;

-- For demo: allow all access (no auth)
-- In production: replace with proper auth.uid() policies

CREATE POLICY "Allow all for demo" ON user_materials FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON user_profiles FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON artifacts FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON feedback FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON background_jobs FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON behavior_signals FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON notifications FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON learning_plans FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON learning_plan_items FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON learning_notes FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON ingestion_jobs FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON user_settings FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON calendar_accounts FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON calendar_calendars FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON calendar_events FOR ALL USING (true);

-- Content items are shared (no RLS needed)

-- ===========================================
-- HELPER FUNCTIONS
-- ===========================================

-- Update profile version on changes (for cache invalidation)
CREATE OR REPLACE FUNCTION update_profile_version()
RETURNS TRIGGER AS $$
BEGIN
  NEW.profile_version := OLD.profile_version + 1;
  NEW.updated_at := NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_profile_version
  BEFORE UPDATE OF style_dna, goals ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_profile_version();
```

---

## Entity Relationship Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  content_items  │     │  user_profiles  │     │    artifacts    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │◄────│ user_id (UNIQUE)│────►│ user_id         │
│ content_hash    │     │ style_dna       │     │ content_ids[]   │───┐
│ title           │     │ goals           │     │ profile_version │   │
│ raw_text        │     │ calendar_context│     │ artifact_type   │   │
│ embedding       │     │ profile_version │     │ content         │   │
│ topics          │     └─────────────────┘     │ priority_score  │   │
│ word_count      │                             └─────────────────┘   │
└─────────────────┘                                     │             │
        ▲                                               │             │
        │                                               ▼             │
        │ FK                                    ┌─────────────────┐   │
┌─────────────────┐                             │    feedback     │   │
│ user_materials  │                             ├─────────────────┤   │
├─────────────────┤                             │ user_id         │   │
│ user_id         │                             │ artifact_id (FK)│◄──┘
│ content_id (FK) │─────────────────────────────│ explicit_rating │
│ storage_path    │                             │ time_spent_secs │
│ status          │                             └─────────────────┘
└─────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ background_jobs │     │behavior_signals │     │  notifications  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ user_id         │     │ user_id         │     │ user_id         │
│ job_type        │     │ signal_type     │     │ channel         │
│ status          │     │ signal_data     │     │ title           │
│ priority        │     │ processed       │     │ body            │
│ payload         │     └─────────────────┘     │ sent            │
└─────────────────┘                             └─────────────────┘
```

---

## Index Summary

| Table | Index | Purpose |
|-------|-------|---------|
| content_items | `idx_content_embedding` | Vector similarity search |
| content_items | `idx_content_hash` | Deduplication lookup |
| user_materials | `idx_user_materials_user` | User's content list |
| user_materials | `idx_user_materials_status` | Processing queue |
| user_profiles | `idx_user_profiles_user` | Profile lookup |
| artifacts | `idx_artifacts_user` | User's artifacts |
| artifacts | `idx_artifacts_cache` | Cache key lookup |
| feedback | `idx_feedback_user` | User feedback history |
| background_jobs | `idx_jobs_status` | Job queue processing |
| behavior_signals | `idx_signals_unprocessed` | Batch processing |
| notifications | `idx_notifications_user` | User notifications |
| notifications | `idx_notifications_unsent` | Send queue |
