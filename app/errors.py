"""Tratamento de erros global — traduz erros tecnicos em mensagens que o GPT narra."""

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
import structlog

logger = structlog.get_logger()

# Mapeamento de erros PostgreSQL para mensagens narrativas
PG_ERROR_MAP = {
    "23503": {"code": "REFERENCE_NOT_FOUND", "msg": "O item referenciado nao existe no banco"},
    "23505": {"code": "ALREADY_EXISTS", "msg": "Este registro ja existe"},
    "23514": {"code": "VALIDATION_FAILED", "msg": "Valor fora do intervalo permitido"},
    "23502": {"code": "REQUIRED_FIELD", "msg": "Campo obrigatorio nao preenchido"},
    "42P01": {"code": "TABLE_NOT_FOUND", "msg": "Recurso nao encontrado no sistema"},
    "42883": {"code": "FUNCTION_NOT_FOUND", "msg": "Funcao do sistema nao encontrada"},
}


class AppException(Exception):
    """Excecao base do Nexus."""

    def __init__(self, code: str, message: str, status_code: int = 400,
                 suggestion: str = None, valid_values: dict = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.suggestion = suggestion
        self.valid_values = valid_values


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier=None):
        suggestion = f"Verifique se o ID de {resource} esta correto"
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} nao encontrado" + (f" (id={identifier})" if identifier else ""),
            status_code=404,
            suggestion=suggestion,
        )


class InsufficientResourceError(AppException):
    def __init__(self, resource: str, required: int, available: int):
        super().__init__(
            code="INSUFFICIENT_RESOURCE",
            message=f"{resource} insuficiente: precisa {required}, tem {available}",
            status_code=400,
            suggestion=f"O personagem precisa recuperar {resource} antes de usar",
        )


class InvalidStateError(AppException):
    def __init__(self, message: str, suggestion: str = None):
        super().__init__(
            code="INVALID_STATE",
            message=message,
            status_code=409,
            suggestion=suggestion,
        )


class CombatPhaseError(AppException):
    def __init__(self, current_phase: str, attempted_action: str):
        super().__init__(
            code="COMBAT_PHASE_ERROR",
            message=f"Nao pode fazer '{attempted_action}' durante fase '{current_phase}'",
            status_code=409,
            suggestion=f"Fase atual: {current_phase}. Avance o turno primeiro.",
        )


def register_error_handlers(app: FastAPI):
    """Registra handlers globais de erro no app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        body = {
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        }
        if exc.suggestion:
            body["error"]["suggestion"] = exc.suggestion
        if exc.valid_values:
            body["error"]["valid_values"] = exc.valid_values

        logger.warning("app_exception", code=exc.code, message=exc.message, path=str(request.url.path))
        return ORJSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Verifica se eh erro PostgreSQL com SQLSTATE
        error_msg = str(exc)
        pg_code = None

        if hasattr(exc, "sqlstate"):
            pg_code = exc.sqlstate
        elif hasattr(exc, "__cause__") and hasattr(exc.__cause__, "sqlstate"):
            pg_code = exc.__cause__.sqlstate

        if pg_code and pg_code in PG_ERROR_MAP:
            mapped = PG_ERROR_MAP[pg_code]
            logger.warning("pg_error_mapped", pg_code=pg_code, mapped_code=mapped["code"])
            return ORJSONResponse(
                status_code=400,
                content={"error": {"code": mapped["code"], "message": mapped["msg"]}},
            )

        logger.error("unhandled_exception", error=error_msg, path=str(request.url.path), exc_info=True)
        return ORJSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "message": "Erro interno do servidor"}},
        )
