# Google Calendar One-Time Sync (Hackathon Mode)

This implementation supports a **one-time Google OAuth connection** followed by a **local cache import** of calendar data. After the sync, all reads use the local `calendar_events` table.

## Environment Variables

```
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/v1/calendar/google/callback
```

## OAuth Flow

1) Get consent URL  
`GET /api/v1/calendar/google/auth-url?user_id=...`  
→ returns `auth_url`

2) User authorizes and Google redirects to  
`GET /api/v1/calendar/google/callback?code=...&state=...`

Tokens are stored in `calendar_accounts.auth_data` (including `refresh_token` and `expires_at`).

## One-Time Sync

`POST /api/v1/calendar/google/sync`

Payload:
```
{
  "user_id": "...",
  "time_min": "2026-02-01T00:00:00Z",
  "time_max": "2026-05-01T00:00:00Z"
}
```

The sync:
- imports calendar metadata into `calendar_calendars`
- imports events into `calendar_events`
- updates existing events by `external_id`

## Local Reads

Use existing endpoints (no Google calls):
- `GET /api/v1/calendar/events`
- `GET /api/v1/calendar/availability`

## Notes

- This is **hackathon mode**: one-time sync, then local cache.
- Re-running `/google/sync` refreshes event data.
