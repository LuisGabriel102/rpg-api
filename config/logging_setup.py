"""
Configuração de logging estruturado (structlog) — Catedral do Alderyn.

DESIGN:
- Em DEV (LOG_FORMAT=console): output colorido legível humano
- Em PROD (LOG_FORMAT=json):   output JSON estruturado (1 linha por evento)
- Nível controlado por LOG_LEVEL no .env (default INFO)
"""

from __future__ import annotations

import logging
import os
import sys

import structlog


_configurado = False


def configurar_logging() -> None:
    """Configura structlog uma única vez (idempotente)."""
    global _configurado
    if _configurado:
        return

    log_format = (os.getenv("LOG_FORMAT") or "console").lower().strip()
    log_level = (os.getenv("LOG_LEVEL") or "INFO").upper().strip()

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level, logging.INFO),
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level, logging.INFO)
        ),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configurado = True


def get_logger(name: str = "catedral") -> structlog.stdlib.BoundLogger:
    """Retorna logger estruturado.

    Example:
        log = get_logger(__name__)
        log.info("api_chamada", modelo="gemini", custo=0.067)
    """
    if not _configurado:
        configurar_logging()
    return structlog.get_logger(name)
