# Note-Triggered Agent Pipeline

System design: any change to a learning note automatically triggers the agent pipeline. There is no manual UI button required.

## Trigger points
- **Create note**: `POST /api/v1/notes`
- **Update note**: `PATCH /api/v1/notes/{note_id}`

## Backend flow
1. Notes API writes to `learning_notes`.
2. Notes API sends a best-effort message to the **orchestrator agent**:
   - event: `created` or `updated`
   - user_id + note_id
   - instruction to schedule background generation

## Rationale
- Keeps UI simple (no explicit “Generate” button).
- Ensures any note change (manual entry, upload-derived, edits) is processed consistently.

## Observability
Because the trigger happens server-side, visibility comes from:
- agent logs (see `AGENT_LOG_LEVEL`)
- `background_jobs` (scheduled by orchestrator)
- `notifications` (written by orchestrator once work completes)

## UI surfaces
- Dashboard: "Latest Materials" shows generated artifacts only.
- Knowledge Bank: top section shows generated materials first.

## Testing checklist
- Create a note via API/UI → confirm `learning_notes` row.
- Check agent logs for trigger.
- Verify a background job or notification is created.
