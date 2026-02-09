#!/usr/bin/env python3
"""
Deterministic video smoke test (kickoff path):
1) Insert a tiny artifact directly into DB
2) Trigger /api/v1/video/generate/{artifact_id}
3) Verify video_artifacts row exists
4) Verify video_segments rows are created
5) Verify /api/v1/video/metadata/{artifact_id} returns progress payload

Note: actual rendering is asynchronous and handled by video worker.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

import asyncpg


DEFAULT_PROMPT = "Create a short educational video concept about potato growth."


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


async def _wait_for_video_rows(dsn: str, artifact_id: str, timeout_s: int = 90) -> Dict[str, Any]:
    conn = await asyncpg.connect(dsn)
    try:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            video_row = await conn.fetchrow(
                """
                SELECT id, status, video_path, duration_seconds, resolution, aspect_ratio
                FROM video_artifacts
                WHERE artifact_id = $1
                """,
                artifact_id,
            )
            if video_row:
                seg_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM video_segments WHERE video_artifact_id = $1",
                    video_row["id"],
                )
                if seg_count and seg_count > 0:
                    return {"video": dict(video_row), "segments": int(seg_count)}
            await asyncio.sleep(2.0)
    finally:
        await conn.close()
    raise TimeoutError(f"No video artifact+segments found for artifact {artifact_id} within {timeout_s}s.")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gateway-url", default=os.getenv("GATEWAY_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--user-id", default=f"video_smoke_{int(time.time())}")
    parser.add_argument("--total-duration", type=int, default=120)
    args = parser.parse_args()

    dsn = os.getenv("SUPABASE_URL", "").strip()
    if not dsn:
        print("ERROR: SUPABASE_URL is required.")
        return 2

    gateway = args.gateway_url.rstrip("/")

    print(f"[1/5] Inserting artifact (user_id={args.user_id})")
    artifact_id = await _insert_artifact(dsn, args.user_id, args.prompt)
    print(f"      artifact_id={artifact_id}")

    print("[2/5] Triggering video generation endpoint")
    kickoff = _http_json(
        "POST",
        f"{gateway}/api/v1/video/generate/{artifact_id}",
        {"user_id": args.user_id, "total_duration": args.total_duration},
    )
    print(f"      endpoint_response_keys={list(kickoff.keys())}")

    print("[3/5] Waiting for video_artifacts + video_segments rows")
    rows = await _wait_for_video_rows(dsn, artifact_id)
    print(
        "      "
        + json.dumps(
            {
                "video_id": str(rows["video"]["id"]),
                "status": rows["video"]["status"],
                "video_path": rows["video"]["video_path"],
                "segments": rows["segments"],
            }
        )
    )

    print("[4/5] Fetching video metadata endpoint")
    metadata = _http_json("GET", f"{gateway}/api/v1/video/metadata/{artifact_id}")
    print(
        "      "
        + json.dumps(
            {
                "status": metadata.get("status"),
                "progress": metadata.get("progress"),
                "current_segment": metadata.get("current_segment"),
                "total_segments": metadata.get("total_segments"),
                "video_url": metadata.get("video_url"),
            }
        )
    )

    print("[5/5] Verifying kickoff expectations")
    if metadata.get("status") not in {"generating", "ready"}:
        print(f"FAIL: unexpected status {metadata.get('status')}")
        return 1
    if rows["segments"] <= 0:
        print("FAIL: no segment rows created")
        return 1
    print("PASS: video generation kickoff and metadata flow verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
