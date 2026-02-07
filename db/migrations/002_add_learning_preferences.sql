-- Migration: Add learning_preferences and custom_style to user_settings
-- These fields are part of the study_preferences JSONB column

-- Update existing study_preferences to include new fields with defaults
UPDATE user_settings
SET study_preferences = jsonb_set(
    jsonb_set(
        COALESCE(study_preferences, '{}'::jsonb),
        '{learning_preferences}',
        '[]'::jsonb,
        true
    ),
    '{custom_style}',
    '""'::jsonb,
    true
)
WHERE study_preferences IS NULL 
   OR NOT (study_preferences ? 'learning_preferences')
   OR NOT (study_preferences ? 'custom_style');

-- Update default tone from 'eli5' to 'textbook' for new users
UPDATE user_settings
SET study_preferences = jsonb_set(
    study_preferences,
    '{tone}',
    '"textbook"'::jsonb,
    true
)
WHERE study_preferences->>'tone' = 'eli5';

-- Add comment explaining the structure
COMMENT ON COLUMN user_settings.study_preferences IS 
'JSONB containing user style DNA preferences:
{
  "tone": "textbook" | "coaching" | "beginner_friendly" | "key_points",
  "format_pref": "outline" | "cornell" | "mindmap",
  "uses_emoji": boolean,
  "prefers_diagrams": boolean,
  "learning_preferences": ["analogies", "real_world", "concept_map", "practice_set"],
  "custom_style": "user custom description"
}';
