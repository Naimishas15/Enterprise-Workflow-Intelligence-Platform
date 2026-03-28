from app.database import get_pool
from app.redis_client import get_redis
from app.services.cost import calculate_cost
import asyncio

async def reconcile(
    tenant_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    query_text: str,
    response_text: str,
    query_embedding: list,
    cached: bool
):
    cost = calculate_cost(model, input_tokens, output_tokens)

    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO audit_log
                (tenant_id, model, input_tokens, output_tokens,
                 cost_usd, latency_ms, cached)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, tenant_id, model, input_tokens, output_tokens,
             cost, latency_ms, cached)

    if not cached and query_embedding:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO semantic_cache
                    (tenant_id, query_embedding, query_text,
                     response_text, model)
                VALUES ($1, $2::vector, $3, $4, $5)
            """, tenant_id, str(query_embedding),
                 query_text, response_text, model)

    r = await get_redis()
    credits_to_deduct = max(1, int(cost * 1000))
    await r.decrby(f"tenant:{tenant_id}:credits", credits_to_deduct - 1)