from fastapi import APIRouter, HTTPException
from app.database import get_pool
from app.redis_client import set_credits, get_credits
from app.models.tenant import TenantCreate, TenantResponse, CreditsAdd
import uuid

router = APIRouter()

@router.post("/tenants", response_model=dict)
async def create_tenant(tenant: TenantCreate):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO tenants (name, plan, credits)
            VALUES ($1, $2, $3)
            RETURNING id, name, plan, credits, is_active, created_at
        """, tenant.name, tenant.plan, tenant.credits)

    tenant_id = str(row["id"])
    await set_credits(tenant_id, row["credits"])

    return {
        "id": tenant_id,
        "name": row["name"],
        "plan": row["plan"],
        "credits": row["credits"],
        "is_active": row["is_active"],
        "created_at": str(row["created_at"])
    }

@router.get("/tenants", response_model=list)
async def list_tenants():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, plan, credits, is_active, created_at
            FROM tenants
            ORDER BY created_at DESC
        """)
    return [
        {
            "id": str(r["id"]),
            "name": r["name"],
            "plan": r["plan"],
            "credits": r["credits"],
            "is_active": r["is_active"],
            "created_at": str(r["created_at"])
        }
        for r in rows
    ]

@router.get("/tenants/{tenant_id}", response_model=dict)
async def get_tenant(tenant_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, name, plan, credits, is_active, created_at
            FROM tenants WHERE id = $1
        """, uuid.UUID(tenant_id))

    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")

    redis_credits = await get_credits(tenant_id)

    return {
        "id": str(row["id"]),
        "name": row["name"],
        "plan": row["plan"],
        "credits_postgres": row["credits"],
        "credits_redis": redis_credits,
        "is_active": row["is_active"],
        "created_at": str(row["created_at"])
    }

@router.post("/tenants/{tenant_id}/credits")
async def add_credits(tenant_id: str, body: CreditsAdd):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            UPDATE tenants
            SET credits = credits + $1
            WHERE id = $2
            RETURNING credits
        """, body.amount, uuid.UUID(tenant_id))

    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")

    await set_credits(tenant_id, row["credits"])

    return {"credits": row["credits"], "added": body.amount}

@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE tenants SET is_active = false WHERE id = $1
        """, uuid.UUID(tenant_id))
    return {"deleted": tenant_id}