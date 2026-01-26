"""
Database helpers for the gateway.

Uses asyncpg with a small connection pool.
"""

from typing import Optional
import asyncpg

from app.core.config import settings

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the global connection pool."""
    global _pool
    if _pool is None:
        if not settings.supabase_url:
            raise RuntimeError("SUPABASE_URL is not set")
        _pool = await asyncpg.create_pool(dsn=settings.supabase_url, min_size=1, max_size=5)
    return _pool


async def fetch(query: str, *args):
    """Fetch rows using the shared pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args):
    """Fetch a single row using the shared pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(query, *args)


async def close_pool():
    """Close the global connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
