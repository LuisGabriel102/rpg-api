"""Middleware: security headers, logging estruturado, deteccao de endpoints lentos."""

import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.config import settings


logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona headers de seguranca em todas as respostas."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if request.url.scheme == "https" or settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Loga cada request com tempo de resposta e detecta endpoints lentos."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        method = request.method
        path = request.url.path

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "request_failed",
                method=method,
                path=path,
                elapsed_ms=round(elapsed_ms, 2),
                error=str(exc),
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        status = response.status_code

        log_data = {
            "method": method,
            "path": path,
            "status": status,
            "elapsed_ms": round(elapsed_ms, 2),
        }

        if elapsed_ms > settings.log_slow_threshold_ms:
            logger.warning("slow_request", **log_data)
        elif status >= 500:
            logger.error("server_error", **log_data)
        elif status >= 400:
            logger.warning("client_error", **log_data)
        else:
            logger.info("request", **log_data)

        response.headers["X-Response-Time-Ms"] = str(round(elapsed_ms, 2))
        return response


def configure_structlog():
    """Configura structlog para output JSON no Railway."""
    import logging
    logging.basicConfig(format="%(message)s", level=logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
