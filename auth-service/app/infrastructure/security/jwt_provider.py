"""Adaptador de emisión/validación de tokens JWT (implementa `TokenProvider`).

Los tokens hacen que el microservicio sea **sin estado**, condición necesaria
para poder replicarlo detrás del balanceador (táctica de redundancia activa).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.domain.entities import TokenClaims, User
from app.domain.exceptions import InvalidToken


class JwtTokenProvider:
    def __init__(self, secret: str, algorithm: str, expiration_minutes: int,
                 issuer: str) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._expiration = timedelta(minutes=expiration_minutes)
        self._issuer = issuer

    def issue(self, user: User) -> tuple[str, datetime]:
        issued_at = datetime.now(timezone.utc)
        expires_at = issued_at + self._expiration
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "iss": self._issuer,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm), expires_at

    def decode(self, token: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token, self._secret, algorithms=[self._algorithm], issuer=self._issuer
            )
            return TokenClaims(
                user_id=UUID(payload["sub"]),
                username=payload["username"],
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
        except jwt.ExpiredSignatureError as exc:
            raise InvalidToken("La sesión expiró") from exc
        except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
            raise InvalidToken() from exc
