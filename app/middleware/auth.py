from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from app.config import settings

async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json",
                         "/tenants", "/tenants/"] or \
    request.url.path.startswith("/tenants/") or \
    request.url.path.startswith("/audit") or \
    request.url.path.startswith("/cache"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"error": "Missing token", "code": "NO_TOKEN"}
        )

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        request.state.tenant_id = payload["sub"]
        request.state.tenant_name = payload.get("name", "")
        request.state.plan = payload.get("plan", "starter")
    except JWTError as e:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid token", "code": "INVALID_TOKEN"}
        )

    return await call_next(request)