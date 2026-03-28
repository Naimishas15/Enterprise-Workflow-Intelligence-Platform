from fastapi import APIRouter
from app.database import get_pool
from app.redis_client import get_redis

router = APIRouter()

@router.get("/health")
async def health():
    status = {"status": "ok", "postgres": "ok", "redis": "ok"}

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as e:
        status["postgres"] = f"error: {str(e)}"
        status["status"] = "degraded"

    try:
        r = await get_redis()
        await r.ping()
    except Exception as e:
        status["redis"] = f"error: {str(e)}"
        status["status"] = "degraded"

    return status