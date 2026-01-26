"""
Ingestion Agent Tools

ADK tools for content ingestion, topic extraction, and embedding generation.
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
    """Get database connection."""
    return await asyncpg.connect(os.getenv("SUPABASE_URL", ""))


def _run_async(coro):
    """Run async coroutine safely, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        # Create a new loop in a thread for nested async calls
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def ingest_content(
    user_id: str,
    content_hash: str,
    filename: str,
    media_type: str,
    content_text: str
) -> Dict[str, Any]:
    """
    Ingest and process uploaded content.
    
    Args:
        user_id: The user who uploaded the content
        content_hash: SHA256 hash of the content for deduplication
        filename: Original filename
        media_type: Type of content (PDF, TXT, MARKDOWN, AUDIO, VIDEO, URL)
        content_text: The text content to process
    
    Returns:
        Dict with status, content_id, material_id, topics, and word_count
    """
    return _run_async(
        _ingest_content_async(user_id, content_hash, filename, media_type, content_text)
    )


async def _ingest_content_async(
    user_id: str,
    content_hash: str,
    filename: str,
    media_type: str,
    content_text: str
) -> Dict[str, Any]:
    """Async implementation of content ingestion."""
    conn = await _get_db_connection()
    
    try:
        # Check for existing content (deduplication)
        existing = await conn.fetchrow(
            "SELECT id FROM content_items WHERE content_hash = $1",
            content_hash
        )
        
        if existing:
            # Link existing content to user
            material_row = await conn.fetchrow(
                """
                INSERT INTO user_materials (user_id, content_id, status)
                VALUES ($1, $2, 'PROCESSED')
                RETURNING id
                """,
                user_id, existing["id"]
            )
            return {
                "status": "success",
                "content_id": str(existing["id"]),
                "material_id": str(material_row["id"]),
                "deduplicated": True
            }
        
        # Extract topics
        topics = await _extract_topics_async(content_text)
        
        # Generate embedding
        embedding = await _generate_embedding_async(content_text)
        
        # Calculate word count
        word_count = len(content_text.split()) if content_text else 0
        
        # Convert embedding list to PostgreSQL vector format string
        # Format: "[0.1, 0.2, 0.3]" for pgvector
        embedding_str = None
        if embedding:
            embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        
        # Store content
        content_row = await conn.fetchrow(
            """
            INSERT INTO content_items 
            (content_hash, title, raw_text, media_type, embedding, topics, word_count)
            VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
            RETURNING id
            """,
            content_hash, filename, content_text, media_type,
            embedding_str, json.dumps(topics) if topics else None, word_count
        )
        content_id = str(content_row["id"])
        
        # Link to user
        material_row = await conn.fetchrow(
            """
            INSERT INTO user_materials (user_id, content_id, status)
            VALUES ($1, $2, 'PROCESSED')
            RETURNING id
            """,
            user_id, content_id
        )
        
        return {
            "status": "success",
            "content_id": content_id,
            "material_id": str(material_row["id"]),
            "topics": topics,
            "word_count": word_count
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        await conn.close()


def extract_topics(text: str) -> Dict[str, Any]:
    """
    Extract key topics from text content.
    
    Args:
        text: The text content to analyze
    
    Returns:
        Dict with status and list of extracted topics
    """
    topics = _run_async(_extract_topics_async(text))
    return {"status": "success", "topics": topics}


async def _extract_topics_async(text: str) -> List[str]:
    """Async implementation of topic extraction using Gemini."""
    if not text or len(text) < 50:
        return []
    
    client = _get_genai_client()
    if not client:
        return []
    
    try:
        prompt = f"""Extract the main topics from this text. Return only a JSON array of strings.
Example output: ["Machine Learning", "Neural Networks", "Python"]

Text:
{text[:5000]}

Return ONLY the JSON array, no other text:"""
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        response_text = response.text
        
        # Parse JSON array from response
        start = response_text.find("[")
        end = response_text.rfind("]") + 1
        if start >= 0 and end > start:
            topics = json.loads(response_text[start:end])
            return topics[:10]
        return []
    except Exception as e:
        print(f"Topic extraction failed: {e}")
        return []


def generate_embedding(text: str) -> Dict[str, Any]:
    """
    Generate vector embedding for text content.
    
    Args:
        text: The text to generate embedding for
    
    Returns:
        Dict with status, embedding vector and dimensions
    """
    embedding = _run_async(_generate_embedding_async(text))
    return {
        "status": "success",
        "embedding": embedding,
        "dimensions": len(embedding) if embedding else 0
    }


async def _generate_embedding_async(text: str) -> Optional[List[float]]:
    """Async implementation of embedding generation."""
    if not text:
        return None
    
    client = _get_genai_client()
    if not client:
        return None
    
    try:
        truncated = text[:8000]
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=truncated
        )
        return result.embeddings[0].values
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        return None
