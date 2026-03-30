"""Cache em memoria para dados de referencia (magias, criaturas, regras, condicoes).
NUNCA cachear estado de jogo (HP, inventario, combate)."""

import time
from typing import Any, Optional
from app.config import settings
import structlog

logger = structlog.get_logger()

_cache: dict[str, dict[str, Any]] = {}


def _is_expired(entry: dict) -> bool:
    return time.time() - entry["ts"] > settings.cache_ttl_seconds


def cache_get(key: str) -> Optional[Any]:
    """Busca valor no cache. Retorna None se nao existe ou expirou."""
    if not settings.cache_enabled:
        return None
    entry = _cache.get(key)
    if entry is None or _is_expired(entry):
        return None
    return entry["value"]


def cache_set(key: str, value: Any) -> None:
    """Armazena valor no cache com TTL."""
    if not settings.cache_enabled:
        return
    _cache[key] = {"value": value, "ts": time.time()}


def cache_invalidate(prefix: str = "") -> int:
    """Invalida entradas que comecam com prefix. Se vazio, limpa tudo."""
    if not prefix:
        count = len(_cache)
        _cache.clear()
        logger.info("cache_cleared", entries_removed=count)
        return count
    keys_to_remove = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_remove:
        del _cache[k]
    logger.info("cache_invalidated", prefix=prefix, entries_removed=len(keys_to_remove))
    return len(keys_to_remove)


def cache_stats() -> dict:
    """Retorna estatisticas do cache."""
    total = len(_cache)
    expired = sum(1 for v in _cache.values() if _is_expired(v))
    return {
        "total_entries": total,
        "active_entries": total - expired,
        "expired_entries": expired,
        "enabled": settings.cache_enabled,
        "ttl_seconds": settings.cache_ttl_seconds,
    }
