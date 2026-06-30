"""Nexus RPG API v3 — Backend do Sistema Nexus D&D 5e + T20.
137 tabelas, 209 RPCs, 2.126 magias, 2.138 criaturas, 42 familias magicas.

Melhorias v3: d20, endpoints compostos, cache, Sentry, structlog, rate limiting,
security headers, compressao, event sourcing, save points, maquina de estados."""

from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from starlette_compress import CompressMiddleware
from asgi_correlation_id import CorrelationIdMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sentry_sdk
import structlog

from app.config import settings
from app.database import pool
from app.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, configure_structlog
from app.errors import register_error_handlers
from app.openapi import custom_openapi
from app.cache import cache_stats, cache_invalidate
from app.auth import verify_token

from app.routers import (
    session, character, combat, magic, npc,
    inventory, progression, world, narrative,
)
from app.routers import dice_router, saves


# === Configurar logging estruturado ===
configure_structlog()
logger = structlog.get_logger()


# === Sentry === (SO em producao: dev tem o DSN no .env, mas nao deve sujar o painel de prod
# com eventos de teste/suite local. Prod: ENVIRONMENT ausente -> default "production" -> liga.)
if settings.sentry_dsn and settings.environment == "production":
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.2,
        environment=settings.environment,
        release=f"nexus-api@{settings.api_version}",
    )
    logger.info("sentry_initialized")
elif settings.sentry_dsn:
    logger.info("sentry_skipped_dev", environment=settings.environment)


# === Rate Limiter ===
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_global])


# === Lifespan ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()
    await pool.check()
    logger.info("pool_opened", min=settings.db_pool_min, max=settings.db_pool_max)
    yield
    await pool.close()
    logger.info("pool_closed")


# === App ===
app = FastAPI(
    title="Nexus RPG API",
    description="Backend do Sistema Nexus D&D 5e + T20. Gerencia personagens, combate, magias, NPCs, ANIMA, maestria e tecnicas.",
    version=settings.api_version,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# === Middleware (ordem importa: ultimo adicionado = primeiro executado) ===
app.add_middleware(CompressMiddleware, minimum_size=1000, gzip_level=5)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")
# === CORS (configurável via env; legado Custom GPT removido) ===
_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
_allow_all = (not _origins) or ("*" in _origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _origins,
    # Wildcard e credentials sao incompativeis no browser: so liga credentials
    # quando as origens sao explicitas (ex: dominio da app NiceGUI).
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*", "X-Request-ID"],
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Error handlers globais
register_error_handlers(app)

# === Routers ===
app.include_router(session.router,      prefix="/api/v1/session",     tags=["Sessao"])
app.include_router(character.router,    prefix="/api/v1/character",   tags=["Personagem"])
app.include_router(combat.router,       prefix="/api/v1/combat",      tags=["Combate"])
app.include_router(magic.router,        prefix="/api/v1/magic",       tags=["Magia"])
app.include_router(npc.router,          prefix="/api/v1/npc",         tags=["NPC"])
app.include_router(inventory.router,    prefix="/api/v1/inventory",   tags=["Inventario"])
app.include_router(progression.router,  prefix="/api/v1/progression", tags=["Progressao"])
app.include_router(world.router,        prefix="/api/v1/world",       tags=["Mundo"])
app.include_router(narrative.router,    prefix="/api/v1/narrative",   tags=["Narrativa"])
app.include_router(dice_router.router,  prefix="/api/v1/dice",        tags=["Dados"])
app.include_router(saves.router,        prefix="/api/v1/saves",       tags=["SavePoints"])


# === Endpoints do sistema ===

@app.get("/health", tags=["Sistema"], include_in_schema=False)
async def health():
    return {"status": "ok", "version": settings.api_version, "system": "Nexus D&D 5e + T20"}


@app.get("/", tags=["Sistema"], include_in_schema=False)
async def root():
    return {
        "name": "Nexus RPG API",
        "version": settings.api_version,
        "system": "Nexus D&D 5e + T20",
        "status": "online",
        "improvements": "v3: d20, compostos, cache, sentry, structlog, rate-limit, compression, events",
    }


@app.get("/cache/stats", tags=["Sistema"], include_in_schema=False)
async def get_cache_stats(_token: str = Depends(verify_token)):
    return cache_stats()


@app.post("/cache/invalidate", tags=["Sistema"], include_in_schema=False)
async def invalidate_cache(prefix: str = "", _token: str = Depends(verify_token)):
    removed = cache_invalidate(prefix)
    return {"status": "cache_invalidated", "entries_removed": removed}


# === OpenAPI customizado ===
app.openapi = custom_openapi(app)
