"""Traducción de excepciones a respuestas HTTP.

Es el borde exterior del microservicio: aquí termina la cadena
`driver -> infraestructura -> dominio -> HTTP`. Ninguna traza interna se filtra
al cliente; la traza completa queda en el log.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import audit, get_logger, request_id_var
from app.domain.exceptions import (
    AccountInactive,
    AccountLocked,
    DomainError,
    InvalidCredentials,
    InvalidToken,
    InvalidUsername,
    UserAlreadyExists,
    UserNotFound,
    WeakPassword,
)
from app.infrastructure.exceptions import DatabaseUnavailable, InfrastructureError

_logger = get_logger("api")

# Mapa explícito excepción de dominio -> código HTTP.
_STATUS_BY_EXCEPTION: dict[type[DomainError], int] = {
    InvalidCredentials: status.HTTP_401_UNAUTHORIZED,
    InvalidToken: status.HTTP_401_UNAUTHORIZED,
    AccountInactive: status.HTTP_403_FORBIDDEN,
    AccountLocked: status.HTTP_423_LOCKED,
    UserAlreadyExists: status.HTTP_409_CONFLICT,
    UserNotFound: status.HTTP_404_NOT_FOUND,
    WeakPassword: status.HTTP_422_UNPROCESSABLE_ENTITY,
    InvalidUsername: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _payload(code: str, message: str, detail: dict | None = None) -> dict:
    return {
        "code": code,
        "message": message,
        "request_id": request_id_var.get(),
        "detail": detail,
    }


def register_error_handlers(app: FastAPI) -> None:

    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError) -> JSONResponse:
        http_status = _STATUS_BY_EXCEPTION.get(type(exc), status.HTTP_400_BAD_REQUEST)
        audit(_logger, "api.error", "FAILURE", component="error_handlers",
              message=exc.message, level=logging.WARNING,
              error_code=exc.code, status_code=http_status, path=request.url.path)
        return JSONResponse(
            status_code=http_status,
            content=_payload(exc.code, exc.message, exc.context or None),
        )

    @app.exception_handler(DatabaseUnavailable)
    async def _db_down(request: Request, exc: DatabaseUnavailable) -> JSONResponse:
        audit(_logger, "api.error", "FAILURE", component="error_handlers",
              message="Dependencia no disponible: base de datos", level=logging.ERROR,
              error_code=exc.code, status_code=503, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_payload(exc.code, "El servicio no está disponible temporalmente"),
        )

    @app.exception_handler(InfrastructureError)
    async def _infra(request: Request, exc: InfrastructureError) -> JSONResponse:
        audit(_logger, "api.error", "FAILURE", component="error_handlers",
              message=exc.message, level=logging.ERROR, exc_info=True,
              error_code=exc.code, status_code=500, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_payload(exc.code, "Error interno al procesar la solicitud"),
        )

    @app.exception_handler(HTTPException)
    async def _http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        # `auth_common` (Taller 2, Requerimiento 9) señala fallas de
        # autenticación/autorización con HTTPException, pero ya trae el
        # sobre uniforme {code,message,request_id,detail} en `exc.detail`
        # — se devuelve tal cual, sin el anidado `{"detail": ...}` por
        # defecto de Starlette, para que sea indistinguible de un
        # DomainError de este mismo servicio.
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            audit(_logger, "api.error", "FAILURE", component="error_handlers",
                  message=str(exc.detail.get("message", "")), level=logging.WARNING,
                  error_code=exc.detail.get("code"), status_code=exc.status_code,
                  path=request.url.path)
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted({str(e["loc"][-1]) for e in exc.errors()})
        audit(_logger, "api.validation", "FAILURE", component="error_handlers",
              message="Petición inválida", level=logging.WARNING,
              error_code="validation_error", status_code=422, fields=fields)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_payload("validation_error", "La solicitud no es válida",
                             {"fields": fields}),
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Red de seguridad: nada sale del proceso sin quedar registrado.
        audit(_logger, "api.error", "FAILURE", component="error_handlers",
              message="Excepción no controlada", level=logging.CRITICAL, exc_info=True,
              error_code=type(exc).__name__, status_code=500, path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_payload("internal_error", "Error interno al procesar la solicitud"),
        )
