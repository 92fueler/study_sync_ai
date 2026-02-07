-- Migration: Add audio artifacts support
-- Creates table for audio metadata and updates artifacts table

-- Create audio_artifacts table
CREATE TABLE IF NOT EXISTS audio_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id UUID NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    audio_path TEXT NOT NULL,
    voice_name TEXT NOT NULL,
    duration_seconds FLOAT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(artifact_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_audio_artifacts_artifact_id ON audio_artifacts(artifact_id);

-- Add audio_url column to artifacts table
ALTER TABLE artifacts 
ADD COLUMN IF NOT EXISTS audio_url TEXT;

-- Add comments
COMMENT ON TABLE audio_artifacts IS 'Stores metadata for generated audio versions of text artifacts using Gemini TTS';
COMMENT ON COLUMN audio_artifacts.voice_name IS 'Gemini TTS voice used (e.g., Kore, Puck, Charon, Fenrir)';
COMMENT ON COLUMN audio_artifacts.duration_seconds IS 'Audio duration in seconds';
COMMENT ON COLUMN audio_artifacts.file_size_bytes IS 'Audio file size in bytes';
COMMENT ON COLUMN artifacts.audio_url IS 'URL path to audio file if generated';
