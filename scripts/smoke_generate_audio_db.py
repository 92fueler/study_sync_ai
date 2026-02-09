#!/usr/bin/env python3
"""
Smoke test: note -> artifact -> audio generation -> DB verification.

Usage:
  python scripts/smoke_generate_audio_db.py
  python scripts/smoke_generate_audio_db.py --prompt "Explain transformers simply"
  python scripts/smoke_generate_audio_db.py --user-id user_123

Environment:
  GATEWAY_URL   (default: http://127.0.0.1:8000)
  SUPABASE_URL  (required for DB verification)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

import asyncpg


DEFAULT_PROMPT = (
    "Explain retrieval-augmented generation (RAG) in simple terms with one practical example."
)


@dataclass
class SmokeConfig:
    gateway_url: str
    supabase_dsn: str
    user_id: str
    prompt: str
    voice_name: str
    cognitive_tone: str
    artifact_timeout_s: int
    audio_timeout_s: int
    poll_interval_s: float


def _http_json(
    method: str, url: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30
) -> Dict[str, Any]:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=body, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} - {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def _create_note(cfg: SmokeConfig) -> Dict[str, Any]:
    url = f"{cfg.gateway_url}/api/v1/notes"
    payload = {
        "user_id": cfg.user_id,
        "note_type": "text",
        "title": "Smoke Test Prompt",
        "description": cfg.prompt,
        "tags": [{"type": "topic", "label": "SmokeTest"}],
        "author": "smoke_test",
    }
    return _http_json("POST", url, payload)


def _list_artifacts(cfg: SmokeConfig) -> Dict[str, Any]:
    qs = urllib.parse.urlencode({"user_id": cfg.user_id})
    url = f"{cfg.gateway_url}/api/v1/artifacts?{qs}"
    return _http_json("GET", url)


def _trigger_audio(cfg: SmokeConfig, artifact_id: str) -> Dict[str, Any]:
    url = f"{cfg.gateway_url}/api/v1/audio/generate/{artifact_id}"
    payload = {"voice_name": cfg.voice_name, "cognitive_tone": cfg.cognitive_tone}
    return _http_json("POST", url, payload)


async def _wait_for_artifact(cfg: SmokeConfig) -> str:
    deadline = time.time() + cfg.artifact_timeout_s
    while time.time() < deadline:
        data = _list_artifacts(cfg)
        items = data.get("items") or []
        if items:
            return str(items[0]["id"])
        await asyncio.sleep(cfg.poll_interval_s)
    raise TimeoutError(
        f"No artifact found for user {cfg.user_id} within {cfg.artifact_timeout_s} seconds."
    )


async def _wait_for_audio_row(cfg: SmokeConfig, artifact_id: str) -> Dict[str, Any]:
    conn = await asyncpg.connect(cfg.supabase_dsn)
    try:
        deadline = time.time() + cfg.audio_timeout_s
        while time.time() < deadline:
            row = await conn.fetchrow(
                """
                SELECT
                  aa.artifact_id,
                  aa.voice_name,
                  aa.audio_path,
                  aa.duration_seconds,
                  aa.file_size_bytes,
                  aa.generated_at,
                  a.audio_url
                FROM audio_artifacts aa
                JOIN artifacts a ON a.id = aa.artifact_id
                WHERE aa.artifact_id = $1
                """,
                artifact_id,
            )
            if row:
                return dict(row)
            await asyncio.sleep(cfg.poll_interval_s)
    finally:
        await conn.close()

    raise TimeoutError(
        f"No audio_artifacts row for artifact {artifact_id} within {cfg.audio_timeout_s} seconds."
    )


def _build_config(args: argparse.Namespace) -> SmokeConfig:
    gateway_url = (args.gateway_url or os.getenv("GATEWAY_URL") or "http://127.0.0.1:8000").rstrip("/")
    supabase_dsn = os.getenv("SUPABASE_URL", "").strip()
    if not supabase_dsn:
        raise RuntimeError("SUPABASE_URL is required for DB verification.")
    user_id = args.user_id or f"smoke_audio_{int(time.time())}"
    prompt = args.prompt or DEFAULT_PROMPT
    return SmokeConfig(
        gateway_url=gateway_url,
        supabase_dsn=supabase_dsn,
        user_id=user_id,
        prompt=prompt,
        voice_name=args.voice_name,
        cognitive_tone=args.cognitive_tone,
        artifact_timeout_s=args.artifact_timeout_s,
        audio_timeout_s=args.audio_timeout_s,
        poll_interval_s=args.poll_interval_s,
    )


async def _run(cfg: SmokeConfig) -> int:
    print(f"[1/4] Creating note for user_id={cfg.user_id}")
    note = _create_note(cfg)
    print(f"      note_id={note.get('id')}")

    print("[2/4] Waiting for generated artifact...")
    artifact_id = await _wait_for_artifact(cfg)
    print(f"      artifact_id={artifact_id}")

    print("[3/4] Triggering audio generation...")
    audio_resp = _trigger_audio(cfg, artifact_id)
    print(f"      audio_response={json.dumps(audio_resp, default=str)[:240]}")

    print("[4/4] Verifying DB row in audio_artifacts...")
    row = await _wait_for_audio_row(cfg, artifact_id)
    print("      DB row found:")
    print(
        json.dumps(
            {
                "artifact_id": str(row.get("artifact_id")),
                "voice_name": row.get("voice_name"),
                "audio_path": row.get("audio_path"),
                "audio_url": row.get("audio_url"),
                "duration_seconds": row.get("duration_seconds"),
                "file_size_bytes": row.get("file_size_bytes"),
                "generated_at": str(row.get("generated_at")),
            },
            indent=2,
        )
    )

    print("\nPASS: text + audio generation verified in DB.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test audio generation and DB persistence.")
    parser.add_argument("--gateway-url", default=None, help="Gateway base URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--user-id", default=None, help="User ID to use (default: auto-generated)")
    parser.add_argument("--prompt", default=None, help="Prompt text (default: built-in RAG prompt)")
    parser.add_argument("--voice-name", default="Kore", help="Voice name for /audio/generate")
    parser.add_argument("--cognitive-tone", default="coaching", help="Cognitive tone for /audio/generate")
    parser.add_argument("--artifact-timeout-s", type=int, default=120, help="Timeout waiting for artifact")
    parser.add_argument("--audio-timeout-s", type=int, default=120, help="Timeout waiting for audio DB row")
    parser.add_argument("--poll-interval-s", type=float, default=3.0, help="Polling interval in seconds")
    args = parser.parse_args()

    try:
        cfg = _build_config(args)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    try:
        return asyncio.run(_run(cfg))
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

