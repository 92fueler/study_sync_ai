-- Migration: Add video artifacts support
-- Description: Creates tables and indexes for storing video generation metadata

-- Create video_artifacts table
CREATE TABLE IF NOT EXISTS video_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    video_path TEXT NOT NULL,
    duration_seconds FLOAT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    resolution TEXT NOT NULL, -- '720p', '1080p', '4k'
    aspect_ratio TEXT NOT NULL, -- '16:9', '9:16'
    prompt TEXT NOT NULL,
    topic_category TEXT, -- 'hard_science', 'humanities', 'soft_skills'
    learning_style TEXT, -- Style used for generation (real_world, analogies, etc.)
    cognitive_tone TEXT, -- Tone used (textbook, coaching, etc.)
    operation_id TEXT, -- Veo async operation ID
    status TEXT DEFAULT 'generating', -- 'generating', 'ready', 'failed'
    error_message TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(artifact_id)
);

-- Create video_segments table for multi-segment videos
CREATE TABLE IF NOT EXISTS video_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_artifact_id UUID NOT NULL REFERENCES video_artifacts(id) ON DELETE CASCADE,
    segment_index INTEGER NOT NULL,
    act_number INTEGER NOT NULL,
    act_style TEXT NOT NULL, -- 'real_world', 'analogies', 'concept_map', 'practice_set'
    segment_path TEXT NOT NULL,
    duration_seconds FLOAT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    prompt TEXT NOT NULL,
    operation_id TEXT, -- Veo async operation ID for this segment
    status TEXT DEFAULT 'generating', -- 'generating', 'ready', 'failed'
    error_message TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(video_artifact_id, segment_index)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_video_artifacts_artifact_id ON video_artifacts(artifact_id);
CREATE INDEX IF NOT EXISTS idx_video_artifacts_status ON video_artifacts(status);
CREATE INDEX IF NOT EXISTS idx_video_artifacts_operation_id ON video_artifacts(operation_id);

CREATE INDEX IF NOT EXISTS idx_video_segments_video_artifact_id ON video_segments(video_artifact_id);
CREATE INDEX IF NOT EXISTS idx_video_segments_status ON video_segments(status);
CREATE INDEX IF NOT EXISTS idx_video_segments_operation_id ON video_segments(operation_id);

-- Add video_url column to artifacts table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'artifacts' AND column_name = 'video_url'
    ) THEN
        ALTER TABLE artifacts ADD COLUMN video_url TEXT;
    END IF;
END $$;

-- Create storage directory (note: this is handled by application code)
-- storage/video/ will be created automatically when first video is generated
