import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_pool, close_pool
from app.redis_client import get_redis
from app.services.embedder import get_embedder
from app.middleware.auth import auth_middleware
from app.middleware.budget import budget_middleware
from app.middleware.cache import cache_middleware
from app.middleware.sanitizer import sanitizer_middleware

from app.routes import gateway, tenants, audit, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await create_pool()
    print("PostgreSQL pool created")
    await get_redis()
    print("Redis connected")
    get_embedder()
    print("Embedder loaded")
    yield
    print("Shutting down...")
    await close_pool()

app = FastAPI(
    title="LLM Gateway",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Register middleware — FastAPI executes in REVERSE order
# So register: sanitizer → cache → budget → auth
# Execution order: auth → budget → cache → sanitizer → route
app.middleware("http")(sanitizer_middleware)
app.middleware("http")(cache_middleware)
app.middleware("http")(budget_middleware)
app.middleware("http")(auth_middleware)

# Routes
app.include_router(gateway.router)
app.include_router(tenants.router)
app.include_router(audit.router)
app.include_router(health.router)