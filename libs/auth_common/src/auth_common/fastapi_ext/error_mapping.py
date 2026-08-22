"""Traduce errores de la librería al contrato HTTP uniforme del taller.

`{code, message, request_id, detail}` — el mismo sobre que ya produce
`auth-service/app/api/error_handlers.py`, para que un 401/403 sea
indistinguible para el cliente venga del `DomainError` de un servicio o de
esta librería.
"""

from __future__ import annotations

from fastapi import HTTPException

from ..errors import AuthCommonError


def to_http_exception(exc: AuthCommonError, request_id: str) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail={
            "code": exc.code,
            "message": exc.message,
            "request_id": request_id,
            "detail": None,
        },
    )
