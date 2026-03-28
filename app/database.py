import asyncpg
from app.config import settings

_pool = None

async def create_pool():
    global _pool
    _pool = await asyncpg.create_pool(
        settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
        min_size=2,
        max_size=10
    )
    return _pool

async def get_pool():
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()

async def get_db():
    async with _pool.acquire() as connection:
        yield connection