"""
Synthesis Agent Tools

ADK tools for generating personalized learning artifacts.
"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional

import asyncpg
from google import genai


# Lazy-initialized Gemini client
_client = None


def _get_genai_client():
    """Get or create the Gemini client lazily."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client


async def _get_db_connection():
    return await asyncpg.connect(os.getenv("SUPABASE_URL", ""))


def _run_async(coro):
    """Run async coroutine safely, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def _build_system_instruction(style_dna: Dict[str, Any]) -> str:
    """Build Gemini system instruction from Style DNA."""
    tone = style_dna.get("tone", "eli5")
    format_pref = style_dna.get("format_pref", "outline")
    uses_emoji = style_dna.get("uses_emoji", False)
    prefers_diagrams = style_dna.get("prefers_diagrams", True)
    
    tone_map = {
        "eli5": "Explain concepts simply, as if to a beginner. Use analogies and everyday examples.",
        "socratic": "Use a questioning approach. Pose thought-provoking questions to guide understanding.",
        "academic": "Use formal, precise language. Include technical terminology and citations where relevant."
    }
    
    format_map = {
        "cornell": "Use Cornell note format with cues, notes, and summary sections.",
        "mindmap": "Organize content hierarchically with clear branches and connections.",
        "outline": "Use a clean outline format with headers, bullet points, and numbered lists."
    }
    
    return f"""You are a study material synthesizer. Create content with these preferences:

TONE: {tone_map.get(tone, tone_map['eli5'])}

FORMAT: {format_map.get(format_pref, format_map['outline'])}

{"EMOJIS: Use emojis to highlight key points and make content engaging." if uses_emoji else "EMOJIS: Do not use emojis."}

{"DIAGRAMS: Include Mermaid diagrams for complex concepts using ```mermaid blocks." if prefers_diagrams else "DIAGRAMS: Focus on text explanations, avoid diagrams."}

Always:
1. Start with a clear overview
2. Break down complex concepts
3. Highlight key takeaways
4. End with a brief summary"""


def generate_artifact(
    user_id: str,
    content_ids: List[str],
    profile_version: int,
    style_dna: Dict[str, Any],
    time_available_minutes: int = 25
) -> Dict[str, Any]:
    """
    Generate a full personalized study artifact.
    
    Args:
        user_id: User identifier
        content_ids: List of source content IDs to synthesize
        profile_version: Profile version for cache key
        style_dna: User's style preferences (tone, format_pref, uses_emoji, prefers_diagrams)
        time_available_minutes: Target reading time
    
    Returns:
        Dict with status, artifact_id, content, content_5min, estimated_minutes
    """
    return _run_async(
        _generate_artifact_async(user_id, content_ids, profile_version, style_dna, time_available_minutes)
    )


async def _generate_artifact_async(
    user_id: str,
    content_ids: List[str],
    profile_version: int,
    style_dna: Dict[str, Any],
    time_available_minutes: int
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        # Check cache
        cached = await conn.fetchrow(
            """
            SELECT * FROM artifacts 
            WHERE user_id = $1 AND content_ids = $2 AND profile_version = $3 AND artifact_type = 'full'
            ORDER BY created_at DESC LIMIT 1
            """,
            user_id, content_ids, profile_version
        )
        
        if cached:
            return {
                "status": "success",
                "artifact_id": str(cached["id"]),
                "content": cached["content"],
                "estimated_minutes": cached.get("estimated_minutes", time_available_minutes),
                "cached": True
            }
        
        # Get source content
        source_texts = []
        for cid in content_ids:
            row = await conn.fetchrow("SELECT raw_text, title FROM content_items WHERE id = $1", cid)
            if row and row.get("raw_text"):
                source_texts.append(row["raw_text"])
        
        if not source_texts:
            return {"status": "error", "error": "No source content found"}
        
        combined = "\n\n---\n\n".join(source_texts)
        system_instruction = _build_system_instruction(style_dna)
        
        # Generate full artifact
        full_prompt = f"""{system_instruction}

Create a comprehensive study note for this content.
Target reading time: {time_available_minutes} minutes.

Source material:
{combined[:15000]}

Generate a well-structured study note matching user preferences."""
        
        full_response = _get_genai_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        full_content = full_response.text
        
        # Generate 5-min version
        five_prompt = f"""{system_instruction}

Condense into a 5-minute quick summary. Focus on key takeaways.

Source:
{combined[:8000]}"""
        
        five_response = _get_genai_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=five_prompt
        )
        five_content = five_response.text
        
        # Estimate time
        word_count = len(full_content.split())
        estimated_minutes = max(1, word_count // 200)
        
        # Store full artifact
        row = await conn.fetchrow(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
            VALUES ($1, $2, $3, 'full', $4, $5)
            RETURNING id
            """,
            user_id, content_ids, profile_version, full_content, estimated_minutes
        )
        artifact_id = str(row["id"])
        
        # Store 5-min artifact
        await conn.execute(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
            VALUES ($1, $2, $3, '5min', $4, 5)
            """,
            user_id, content_ids, profile_version, five_content
        )
        
        return {
            "status": "success",
            "artifact_id": artifact_id,
            "content": full_content,
            "content_5min": five_content,
            "estimated_minutes": estimated_minutes,
            "cached": False
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def generate_5min_summary(
    user_id: str,
    content_id: str,
    profile_version: int,
    style_dna: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate only a 5-minute summary.
    
    Args:
        user_id: User identifier
        content_id: Single content ID to summarize
        profile_version: Profile version for cache
        style_dna: User's style preferences
    
    Returns:
        Dict with status, artifact_id, content, estimated_minutes (always 5)
    """
    return _run_async(
        _generate_5min_async(user_id, content_id, profile_version, style_dna)
    )


async def _generate_5min_async(
    user_id: str,
    content_id: str,
    profile_version: int,
    style_dna: Dict[str, Any]
) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT raw_text FROM content_items WHERE id = $1", content_id)
        if not row:
            return {"status": "error", "error": "Content not found"}
        
        system_instruction = _build_system_instruction(style_dna)
        
        prompt = f"""{system_instruction}

Create a 5-minute quick summary. Focus on the most important points.

Source:
{row['raw_text'][:8000]}"""
        
        response = _get_genai_client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        artifact_row = await conn.fetchrow(
            """
            INSERT INTO artifacts (user_id, content_ids, profile_version, artifact_type, content, estimated_minutes)
            VALUES ($1, $2, $3, '5min', $4, 5)
            RETURNING id
            """,
            user_id, [content_id], profile_version, response.text
        )
        
        return {
            "status": "success",
            "artifact_id": str(artifact_row["id"]),
            "content": response.text,
            "estimated_minutes": 5
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def get_artifact(artifact_id: str) -> Dict[str, Any]:
    """
    Get a specific artifact by ID.
    
    Args:
        artifact_id: The artifact UUID
    
    Returns:
        Dict with status and artifact details or error
    """
    return _run_async(_get_artifact_async(artifact_id))


async def _get_artifact_async(artifact_id: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM artifacts WHERE id = $1", artifact_id)
        if not row:
            return {"status": "error", "error": "Artifact not found"}
        return {
            "status": "success",
            "id": str(row["id"]),
            "content": row["content"],
            "artifact_type": row["artifact_type"],
            "estimated_minutes": row.get("estimated_minutes"),
            "created_at": str(row["created_at"])
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def list_artifacts(user_id: str, artifact_type: Optional[str] = None) -> Dict[str, Any]:
    """
    List artifacts for a user.
    
    Args:
        user_id: User identifier
        artifact_type: Filter by type ('full', '5min', 'quiz') - optional
    
    Returns:
        Dict with status and list of artifact summaries
    """
    return _run_async(_list_artifacts_async(user_id, artifact_type))


async def _list_artifacts_async(user_id: str, artifact_type: str) -> Dict[str, Any]:
    conn = await _get_db_connection()
    try:
        if artifact_type:
            rows = await conn.fetch(
                "SELECT id, artifact_type, estimated_minutes, created_at FROM artifacts WHERE user_id = $1 AND artifact_type = $2 ORDER BY created_at DESC",
                user_id, artifact_type
            )
        else:
            rows = await conn.fetch(
                "SELECT id, artifact_type, estimated_minutes, created_at FROM artifacts WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
        return {
            "status": "success",
            "artifacts": [
                {"id": str(r["id"]), "artifact_type": r["artifact_type"], "estimated_minutes": r.get("estimated_minutes"), "created_at": str(r["created_at"])}
                for r in rows
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()
