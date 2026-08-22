"""Claims decodificados de un JWT (independiente de framework)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TokenClaims:
    sub: str
    username: str
    role: str
    aud: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    issuer: str
