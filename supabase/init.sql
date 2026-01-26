-- ===========================================
-- StudySync AI Database Schema
-- ===========================================

-- EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ===========================================
-- 1. CONTENT ITEMS (Shared across users)
-- ===========================================
CREATE TABLE content_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  content_hash TEXT UNIQUE NOT NULL,
  title TEXT,
  raw_text TEXT,
  media_type TEXT CHECK (media_type IN ('PDF', 'TXT', 'MARKDOWN', 'AUDIO', 'VIDEO', 'URL')),
  embedding vector(768),
  topics JSONB,
  word_count INT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_content_embedding ON content_items 
  USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_content_hash ON content_items(content_hash);

-- ===========================================
-- 2. USER MATERIALS (Links users to content)
-- ===========================================
CREATE TABLE user_materials (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  content_id UUID REFERENCES content_items(id) ON DELETE CASCADE,
  storage_path TEXT,
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
  style_dna JSONB DEFAULT '{
    "format_pref": "outline",
    "tone": "eli5",
    "uses_emoji": false,
    "prefers_diagrams": true
  }'::jsonb,
  goals JSONB DEFAULT '[]'::jsonb,
  calendar_context JSONB,
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
  content_ids UUID[] NOT NULL,
  profile_version INT NOT NULL,
  artifact_type TEXT NOT NULL CHECK (artifact_type IN ('full', '5min', 'podcast', 'quiz')),
  format TEXT DEFAULT 'text' CHECK (format IN ('text', 'audio')),
  content TEXT NOT NULL,
  estimated_minutes INT,
  priority_score FLOAT,
  priority_reasoning TEXT,
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
  explicit_rating INT CHECK (explicit_rating BETWEEN 1 AND 5),
  time_spent_seconds INT,
  scroll_depth_percent INT,
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
    'generate_5min_new',
    'generate_full_new',
    'regenerate_existing',
    'recalc_priority',
    'send_notification'
  )),
  status TEXT DEFAULT 'QUEUED' CHECK (status IN (
    'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'
  )),
  priority TEXT DEFAULT 'NORMAL' CHECK (priority IN ('HIGH', 'NORMAL', 'LOW')),
  payload JSONB,
  attempts INT DEFAULT 0,
  max_attempts INT DEFAULT 3,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
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
    'skip', 'partial_read', 'complete', 'feedback', 'goal_change', 'style_change'
  )),
  signal_data JSONB,
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
  data JSONB,
  sent BOOLEAN DEFAULT FALSE,
  read BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, read);
CREATE INDEX idx_notifications_unsent ON notifications(sent) WHERE NOT sent;

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

-- For demo: allow all access
CREATE POLICY "Allow all for demo" ON user_materials FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON user_profiles FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON artifacts FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON feedback FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON background_jobs FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON behavior_signals FOR ALL USING (true);
CREATE POLICY "Allow all for demo" ON notifications FOR ALL USING (true);

-- ===========================================
-- HELPER FUNCTIONS
-- ===========================================
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
