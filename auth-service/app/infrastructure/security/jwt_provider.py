"""Adaptador de emisión/validación de tokens JWT (implementa `TokenProvider`).

Delegación fina sobre `auth_common` (Taller 2, Requerimiento 9): la lógica de
codificación/decodificación de tokens vive en la librería compartida —
`auth-service` es, igual que `web` y `products-service`, solo un consumidor
de ella. Este adaptador únicamente traduce configuración y errores para
mantener el puerto `TokenProvider` (y por tanto `application/`) sin cambios.

Los tokens hacen que el microservicio sea **sin estado**, condición necesaria
para poder replicarlo detrás del balanceador (táctica de redundancia activa).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Sequence
from uuid import UUID

from auth_common.errors import AuthCommonError
from auth_common.tokens import decode_token, encode_token

from app.domain.entities import TokenClaims, User
from app.domain.exceptions import InvalidToken


class JwtTokenProvider:
    def __init__(self, secret: str, algorithm: str, expiration_minutes: int,
                 issuer: str, audiences: Sequence[str] = ("auth-service",)) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expiration = timedelta(minutes=expiration_minutes)
        self._issuer = issuer
        self._audiences = tuple(audiences)

    def issue(self, user: User) -> tuple[str, datetime]:
        return encode_token(
            subject=str(user.id),
            username=user.username,
            role=user.role,
            audience=self._audiences,
            secret=self._secret,
            algorithm=self._algorithm,
            issuer=self._issuer,
            expires_in=self._expiration,
        )

    def decode(self, token: str) -> TokenClaims:
        """Decodificación sin exigir audiencia: la usa `/verify`, consumido
        por `web`, que valida la sesión pero no es en sí un resource server.
        La exigencia de audiencia vive en `require_auth` (ver
        `app/api/dependencies.py`), usada por endpoints que sí lo son."""
        try:
            claims = decode_token(
                token, secret=self._secret, algorithm=self._algorithm,
                issuer=self._issuer, expected_audience=None,
            )
        except AuthCommonError as exc:
            raise InvalidToken(exc.message) from exc

        return TokenClaims(
            user_id=UUID(claims.sub),
            username=claims.username,
            expires_at=claims.expires_at,
        )
