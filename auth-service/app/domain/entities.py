"""Entidades del dominio.

Objetos puros de Python: no dependen de FastAPI, SQLAlchemy ni de nada externo.
Contienen el estado y las reglas invariantes del negocio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID


@dataclass
class User:
    username: str
    email: str
    password_hash: str
    id: UUID | None = None
    is_active: bool = True
    role: str = "user"
    failed_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # --- Reglas de bloqueo (táctica de prevención de fallas) ---

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and _aware(self.locked_until) > now

    def seconds_locked(self, now: datetime) -> int:
        if not self.is_locked(now):
            return 0
        return max(1, int((_aware(self.locked_until) - now).total_seconds()))

    def register_failed_attempt(self, now: datetime, max_attempts: int,
                                lockout_seconds: int) -> None:
        """Suma un intento fallido y bloquea la cuenta si se supera el umbral."""
        self.failed_attempts += 1
        if self.failed_attempts >= max_attempts:
            self.locked_until = now + timedelta(seconds=lockout_seconds)

    def register_successful_login(self, now: datetime) -> None:
        self.failed_attempts = 0
        self.locked_until = None
        self.last_login_at = now


def _aware(value: datetime) -> datetime:
    """Normaliza a UTC: SQLite devuelve datetimes sin zona horaria."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class AuthenticatedSession:
    """Resultado de un login exitoso."""

    user_id: UUID
    username: str
    email: str
    access_token: str
    expires_at: datetime


@dataclass(frozen=True)
class TokenClaims:
    user_id: UUID
    username: str
    expires_at: datetime
