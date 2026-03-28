import redis.asyncio as redis
from app.config import settings

_client = None

async def get_redis():
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL)
    return _client

async def get_credits(tenant_id: str) -> int:
    r = await get_redis()
    val = await r.get(f"tenant:{tenant_id}:credits")
    return int(val) if val else 0

async def decr_credits(tenant_id: str) -> int:
    r = await get_redis()
    return await r.decr(f"tenant:{tenant_id}:credits")

async def incr_credits(tenant_id: str) -> int:
    r = await get_redis()
    return await r.incr(f"tenant:{tenant_id}:credits")

async def set_credits(tenant_id: str, amount: int):
    r = await get_redis()
    await r.set(f"tenant:{tenant_id}:credits", amount)