from fastapi import Request
from fastapi.responses import JSONResponse
from app.redis_client import decr_credits, incr_credits, get_credits

async def budget_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
        return await call_next(request)

    if not request.url.path.startswith("/v1/"):
        return await call_next(request)

    tenant_id = request.state.tenant_id

    remaining = await decr_credits(tenant_id)

    if remaining < 0:
        await incr_credits(tenant_id)
        return JSONResponse(
            status_code=429,
            content={
                "error": "Insufficient credits",
                "code": "NO_CREDITS",
                "credits_remaining": 0
            }
        )

    request.state.credits_before = remaining + 1
    return await call_next(request)