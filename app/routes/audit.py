from fastapi import APIRouter, Request
from app.database import get_pool

router = APIRouter()

@router.get("/audit")
async def get_audit(limit: int = 50, tenant_id: str = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tenant_id:
            rows = await conn.fetch("""
                SELECT id, tenant_id, model, input_tokens, output_tokens,
                       cost_usd, latency_ms, cached, created_at
                FROM audit_log
                WHERE tenant_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, tenant_id, limit)
        else:
            rows = await conn.fetch("""
                SELECT id, tenant_id, model, input_tokens, output_tokens,
                       cost_usd, latency_ms, cached, created_at
                FROM audit_log
                ORDER BY created_at DESC
                LIMIT $1
            """, limit)

    return [
        {
            "id": str(r["id"]),
            "tenant_id": str(r["tenant_id"]),
            "model": r["model"],
            "input_tokens": r["input_tokens"],
            "output_tokens": r["output_tokens"],
            "cost_usd": float(r["cost_usd"]) if r["cost_usd"] else 0,
            "latency_ms": r["latency_ms"],
            "cached": r["cached"],
            "created_at": str(r["created_at"])
        }
        for r in rows
    ]

@router.get("/audit/cost-summary")
async def cost_summary():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                t.name as tenant_name,
                a.tenant_id,
                COUNT(*) as total_requests,
                SUM(a.cost_usd) as total_cost,
                AVG(a.latency_ms) as avg_latency,
                SUM(CASE WHEN a.cached THEN 1 ELSE 0 END) as cache_hits
            FROM audit_log a
            JOIN tenants t ON a.tenant_id = t.id
            GROUP BY a.tenant_id, t.name
            ORDER BY total_cost DESC
        """)

    return [
        {
            "tenant_name": r["tenant_name"],
            "tenant_id": str(r["tenant_id"]),
            "total_requests": r["total_requests"],
            "total_cost_usd": float(r["total_cost"]) if r["total_cost"] else 0,
            "avg_latency_ms": round(float(r["avg_latency"]), 1) if r["avg_latency"] else 0,
            "cache_hits": r["cache_hits"],
            "cache_hit_rate": round(r["cache_hits"] / r["total_requests"] * 100, 1)
        }
        for r in rows
    ]

@router.get("/cache/stats")
async def cache_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_entries,
                SUM(hit_count) as total_hits,
                AVG(hit_count) as avg_hits
            FROM semantic_cache
        """)

    return {
        "total_cached_entries": row["total_entries"],
        "total_cache_hits": row["total_hits"] or 0,
        "avg_hits_per_entry": round(float(row["avg_hits"]), 2) if row["avg_hits"] else 0
    }

@router.delete("/cache")
async def clear_cache(tenant_id: str = None):
    pool = await get_pool()
    async with pool.acquire() as conn:
        if tenant_id:
            await conn.execute(
                "DELETE FROM semantic_cache WHERE tenant_id = $1", tenant_id
            )
        else:
            await conn.execute("DELETE FROM semantic_cache")
    return {"cleared": True, "tenant_id": tenant_id or "all"}