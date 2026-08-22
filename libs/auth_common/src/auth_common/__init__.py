"""Librería de autenticación reutilizable (Taller 2, Requerimiento 9).

El núcleo (`tokens`, `claims`, `errors`, `settings`) no depende de ningún
framework. Las integraciones de FastAPI viven en `auth_common.fastapi_ext` y
requieren el extra `auth-common[fastapi]`.
"""

from __future__ import annotations

from .claims import TokenClaims
from .errors import (
    AudienceError,
    AuthCommonError,
    ExpiredTokenError,
    InvalidTokenError,
    OwnershipForbiddenError,
    RoleForbiddenError,
)
from .settings import AuthCommonSettings
from .tokens import decode_token, encode_token

__all__ = [
    "TokenClaims",
    "AudienceError",
    "AuthCommonError",
    "ExpiredTokenError",
    "InvalidTokenError",
    "OwnershipForbiddenError",
    "RoleForbiddenError",
    "AuthCommonSettings",
    "decode_token",
    "encode_token",
]
