from fastapi import Request
from fastapi.responses import JSONResponse
from app.services.embedder import embed
from app.database import get_pool
import json

SIMILARITY_THRESHOLD = 0.95

async def cache_middleware(request: Request, call_next):
    if not request.url.path.startswith("/v1/chat"):
        return await call_next(request)

    body_bytes = await request.body()
    try:
        body = json.loads(body_bytes)
    except Exception:
        return await call_next(request)

    messages = body.get("messages", [])
    if not messages:
        return await call_next(request)

    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        None
    )
    if not last_user_msg:
        return await call_next(request)

    tenant_id = request.state.tenant_id
    query_embedding = embed(last_user_msg)

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, response_text,
                   1 - (query_embedding <=> $1::vector) AS similarity
            FROM semantic_cache
            WHERE tenant_id = $2
              AND 1 - (query_embedding <=> $1::vector) >= $3
            ORDER BY similarity DESC
            LIMIT 1
        """, str(query_embedding), str(tenant_id), SIMILARITY_THRESHOLD)

    if row:
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE semantic_cache
                SET hit_count = hit_count + 1
                WHERE id = $1
            """, row["id"])

        return JSONResponse(content={
            "id": "cache-hit",
            "object": "chat.completion",
            "cached": True,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": row["response_text"]
                },
                "finish_reason": "stop",
                "index": 0
            }]
        })

    request.state.cache_hit = False
    request.state.query_text = last_user_msg
    request.state.query_embedding = query_embedding
    request.state.body_bytes = body_bytes

    return await call_next(request)