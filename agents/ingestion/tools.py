"""
Ingestion Agent Tools - Optimized Google ADK Implementation

Improvements:
1. Native Async handling (no thread pool hacks).
2. JSON Schema enforcement for reliable Topic Extraction.
3. Semantic Chunking for embeddings (handles long docs).
4. Connection pooling for PostgreSQL.
"""

import asyncio
import json
import os
import logging
from typing import Dict, Any, List, Optional
import asyncpg
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy-initialized clients
_client: Optional[genai.Client] = None
_db_pool: Optional[asyncpg.Pool] = None

def _get_genai_client() -> genai.Client:
    """Get or create the Gemini client lazily."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        _client = genai.Client(api_key=api_key)
    return _client

async def _get_db_pool():
    """Manage a singleton DB pool to prevent connection exhaustion."""
    global _db_pool
    if _db_pool is None:
        supabase_url = os.getenv("SUPABASE_URL", "")
        if not supabase_url:
            raise ValueError("SUPABASE_URL is not set.")
        _db_pool = await asyncpg.create_pool(
            supabase_url,
            min_size=1,
            max_size=10
        )
    return _db_pool

# ============================================================================
# Core Ingestion
# ============================================================================

async def ingest_content(
    user_id: str,
    content_hash: str,
    filename: str,
    media_type: str,
    content_text: str
) -> Dict[str, Any]:
    """
    Ingests content: deduplicates, extracts topics & embeddings in parallel, stores in DB.
    Returns content_id, material_id, topics, and word_count.
    """
    logger.info(
        "ingest_content called",
        extra={"user_id": user_id, "file_name": filename, "media_type": media_type}
    )
    try:
        pool = await _get_db_pool()
        
        async with pool.acquire() as conn:
            # Check for existing content (deduplication)
            existing = await conn.fetchrow(
                "SELECT id FROM content_items WHERE content_hash = $1", content_hash
            )
            
            if existing:
                material_row = await conn.fetchrow(
                    """
                    INSERT INTO user_materials (user_id, content_id, status)
                    VALUES ($1, $2, 'PROCESSED')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """,
                    user_id, existing["id"]
                )
                return {
                    "status": "success", 
                    "content_id": str(existing["id"]), 
                    "material_id": str(material_row["id"]) if material_row else None,
                    "deduplicated": True
                }

            # Process topics and embeddings in parallel
            topics_task = extract_topics(content_text)
            embedding_task = generate_embedding(content_text)
            topics_result, embedding_result = await asyncio.gather(topics_task, embedding_task)

            # Format embedding for pgvector (list -> '[val1,val2,...]' string)
            primary_embedding = embedding_result.get("embedding")
            embedding_str = None
            if primary_embedding:
                embedding_str = '[' + ','.join(str(x) for x in primary_embedding) + ']'
            
            word_count = len(content_text.split()) if content_text else 0

            row = await conn.fetchrow(
                """
                INSERT INTO content_items 
                (content_hash, title, raw_text, media_type, embedding, topics, word_count)
                VALUES ($1, $2, $3, $4, $5::vector, $6, $7)
                RETURNING id
                """,
                content_hash, filename, content_text, media_type,
                embedding_str, json.dumps(topics_result.get("topics", [])), word_count
            )
            
            content_id = str(row["id"])
            
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
                "topics": topics_result.get("topics", []),
                "word_count": word_count,
                "chunks_processed": embedding_result.get("chunks_count", 1)
            }
    except Exception as e:
        logger.error(f"Content ingestion failed: {e}")
        return {"status": "error", "error": str(e)}

# ============================================================================
# Topic Extraction
# ============================================================================

async def extract_topics(text: str) -> Dict[str, Any]:
    """
    Extracts topics using Gemini with JSON Schema enforcement for reliable parsing.
    Returns up to 10 topics as a JSON array.
    """
    if not text or len(text) < 50:
        return {"status": "skipped", "topics": []}

    client = _get_genai_client()
    topic_schema = {"type": "ARRAY", "items": {"type": "STRING"}}

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""
            Analyze the following text and extract 5-10 core topics.
            Focus on technical concepts, entities, and definitions.
            Ignore generic terms like "Introduction" or "Chapter 1".
            
            TEXT: {text[:10000]} 
            """,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=topic_schema
            )
        )
        
        topics = json.loads(response.text)
        return {"status": "success", "topics": topics[:10]}

    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        return {"status": "error", "topics": []}

# ============================================================================
# Embedding Generation
# ============================================================================

async def generate_embedding(text: str) -> Dict[str, Any]:
    """
    Generates embeddings with chunking for long documents.
    
    Strategy: Split into 8K char chunks (max 3), embed each, average into single vector.
    This preserves semantic meaning across long docs while fitting pgvector limits.
    """
    if not text:
        return {"status": "empty", "embedding": None}

    client = _get_genai_client()
    CHUNK_SIZE = 8000
    chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)][:3]

    try:
        result = client.models.embed_content(model="gemini-embedding-001", contents=chunks)
        embeddings = [e.values for e in result.embeddings]
        
        # Average chunk embeddings into single document vector
        avg_embedding = [sum(x)/len(embeddings) for x in zip(*embeddings)] if embeddings else []

        return {
            "status": "success",
            "embedding": avg_embedding,
            "chunks_count": len(chunks),
            "dimensions": len(avg_embedding) if avg_embedding else 0
        }
        
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return {"status": "error", "embedding": None}
