#!/usr/bin/env python3
"""
Deterministic audio smoke test:
1) Insert a tiny artifact directly into DB from a fixed prompt
2) Trigger /api/v1/audio/generate/{artifact_id}
3) Verify audio_artifacts row exists
4) Verify file exists on disk
5) Verify audio stream endpoint returns 200 audio/wav
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

import asyncpg


DEFAULT_PROMPT = "Explain potato photosynthesis in two short sentences."


def _http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code} - {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def _http_get_binary(url: str, out_file: Path) -> Dict[str, Any]:
    req = urllib.request.Request(url=url, method="GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
        out_file.write_bytes(data)
        return {
            "status": resp.status,
            "content_type": resp.headers.get("Content-Type", ""),
            "bytes": len(data),
        }


async def _insert_artifact(dsn: str, user_id: str, prompt: str) -> str:
    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, format, content)
            VALUES ($1, ARRAY[]::uuid[], 1, 'full', 'text', $2)
            RETURNING id
            """,
            user_id,
            prompt,
        )
        return str(row["id"])
    finally:
        await conn.close()


async def _wait_for_audio_row(dsn: str, artifact_id: str, timeout_s: int = 120) -> Dict[str, Any]:
    conn = await asyncpg.connect(dsn)
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            row = await conn.fetchrow(
                """
                SELECT aa.audio_path, aa.voice_name, aa.duration_seconds, aa.file_size_bytes, a.audio_url
                FROM audio_artifacts aa
                JOIN artifacts a ON a.id = aa.artifact_id
                WHERE aa.artifact_id = $1
                """,
                artifact_id,
            )
            if row:
                return dict(row)
            await asyncio.sleep(2.0)
    finally:
        await conn.close()
    raise TimeoutError(f"No audio row found for artifact {artifact_id} within {timeout_s}s.")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-url", default=os.getenv("GATEWAY_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--user-id", default=f"audio_smoke_{int(time.time())}")
    parser.add_argument("--voice-name", default="Kore")
    parser.add_argument("--cognitive-tone", default="coaching")
    args = parser.parse_args()

    dsn = os.getenv("SUPABASE_URL", "").strip()
    if not dsn:
        print("ERROR: SUPABASE_URL is required.")
        return 2

    gateway = args.gateway_url.rstrip("/")
    repo_root = Path(__file__).resolve().parents[1]

    print(f"[1/5] Inserting artifact (user_id={args.user_id})")
    artifact_id = await _insert_artifact(dsn, args.user_id, args.prompt)
    print(f"      artifact_id={artifact_id}")

    print("[2/5] Triggering audio generation endpoint")
    response = _http_json(
        "POST",
        f"{gateway}/api/v1/audio/generate/{artifact_id}",
        {
            "voice_name": args.voice_name,
            "cognitive_tone": args.cognitive_tone,
        },
    )
    print(f"      endpoint_response_keys={list(response.keys())}")

    print("[3/5] Waiting for audio row in DB")
    row = await _wait_for_audio_row(dsn, artifact_id)
    print(
        "      "
        + json.dumps(
            {
                "audio_path": row["audio_path"],
                "audio_url": row["audio_url"],
                "voice_name": row["voice_name"],
                "duration_seconds": row["duration_seconds"],
                "file_size_bytes": row["file_size_bytes"],
            }
        )
    )

    print("[4/5] Verifying output file exists on disk")
    audio_rel = Path(str(row["audio_path"]))
    audio_abs = audio_rel if audio_rel.is_absolute() else repo_root / audio_rel
    if not audio_abs.exists():
        print(f"FAIL: audio file not found at {audio_abs}")
        return 1
    print(f"      file={audio_abs} size={audio_abs.stat().st_size}")

    print("[5/5] Verifying stream endpoint")
    audio_url = f"{gateway}{row['audio_url']}"
    stream_out = Path("/tmp/studysync-smoke-audio.wav")
    stream = _http_get_binary(audio_url, stream_out)
    print(f"      stream={stream} out={stream_out}")
    if stream["status"] != 200 or "audio/wav" not in stream["content_type"]:
        print("FAIL: stream endpoint did not return audio/wav")
        return 1

    print("PASS: audio generation + DB persistence + stream verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
