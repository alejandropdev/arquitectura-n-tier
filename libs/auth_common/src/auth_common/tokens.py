"""Núcleo puro de emisión/validación de JWT — sin dependencias de framework.

`decode_token` es el mecanismo detrás del Requerimiento 9(b): cuando se pasa
`expected_audience`, PyJWT exige que ese valor esté en el claim `aud` del
token (que siempre se emite como lista, ver `encode_token`), de modo que un
token emitido para un servicio no sirve para autenticarse contra otro.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

import jwt

from .claims import TokenClaims
from .errors import AudienceError, ExpiredTokenError, InvalidTokenError


def encode_token(
    *,
    subject: str,
    username: str,
    role: str,
    audience: Sequence[str],
    secret: str,
    algorithm: str,
    issuer: str,
    expires_in: timedelta,
    now: datetime | None = None,
) -> tuple[str, datetime]:
    # Se trunca a segundos porque el claim `exp` del JWT solo tiene precisión
    # de segundos (jwt.encode lo serializa como entero) — así el
    # `expires_at` devuelto aquí coincide exactamente con el que se obtiene
    # al decodificar el mismo token más adelante.
    issued_at = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    expires_at = issued_at + expires_in
    payload = {
        "sub": subject,
        "username": username,
        "role": role,
        "aud": list(audience),
        "iss": issuer,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token, expires_at


def decode_token(
    token: str,
    *,
    secret: str,
    algorithm: str,
    issuer: str,
    expected_audience: str | None = None,
) -> TokenClaims:
    """Verifica firma, `iss` y `exp`. Si `expected_audience` se indica,
    exige que sea miembro del `aud` del token (`AudienceError` si no)."""
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            issuer=issuer,
            audience=expected_audience,
            options={"verify_aud": expected_audience is not None},
        )
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("El token expiró") from exc
    except jwt.InvalidAudienceError as exc:
        raise AudienceError("El token no es válido para este servicio") from exc
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise InvalidTokenError("Token inválido") from exc

    try:
        return TokenClaims(
            sub=str(payload["sub"]),
            username=str(payload["username"]),
            role=str(payload.get("role", "user")),
            aud=tuple(payload.get("aud") or ()),
            issued_at=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            issuer=str(payload.get("iss", issuer)),
        )
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("Token inválido") from exc
