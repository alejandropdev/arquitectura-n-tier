"""Errores de la librería, agnósticos de framework.

Cada servicio los traduce a su propio contrato HTTP (ver
`fastapi_ext/error_mapping.py` para la traducción a FastAPI que usan
`auth-service` y `web`).
"""

from __future__ import annotations


class AuthCommonError(Exception):
    """Raíz de toda falla de autenticación/autorización de esta librería."""

    code: str = "auth_error"
    http_status: int = 401

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidTokenError(AuthCommonError):
    code = "invalid_token"


class ExpiredTokenError(AuthCommonError):
    code = "invalid_token"


class AudienceError(AuthCommonError):
    """El token es válido pero no fue emitido para este servicio (`aud`)."""

    code = "invalid_audience"


class RoleForbiddenError(AuthCommonError):
    code = "forbidden"
    http_status = 403


class OwnershipForbiddenError(AuthCommonError):
    code = "forbidden"
    http_status = 403
