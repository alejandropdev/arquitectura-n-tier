"""Puertos (interfaces) que la capa de aplicación necesita.

La capa de aplicación depende de estas abstracciones, no de sus adaptadores
concretos de infraestructura. Esto permite probar los casos de uso con dobles y
cambiar de motor de base de datos o de algoritmo de hash sin tocar el negocio.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.entities import TokenClaims, User


class UserRepository(Protocol):
    """Puerto hacia el Tier 3 (datos)."""

    def get_by_username(self, username: str) -> User | None: ...

    def get_by_id(self, user_id: UUID) -> User | None: ...

    def exists(self, username: str, email: str) -> str | None:
        """Devuelve el campo en conflicto ('username' / 'email') o None."""
        ...

    def add(self, user: User) -> User: ...

    def update(self, user: User) -> None: ...

    def record_login_attempt(self, username: str, successful: bool, client_ip: str,
                             request_id: str, reason: str | None = None) -> None:
        """Bitácora de auditoría persistida (quién / cuándo / qué)."""
        ...


class UnitOfWork(Protocol):
    """Transacción por caso de uso: commit al final, rollback ante cualquier falla."""

    users: UserRepository

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, exc_type, exc, tb) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, plain: str) -> str: ...

    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenProvider(Protocol):
    def issue(self, user: User) -> tuple[str, datetime]: ...

    def decode(self, token: str) -> TokenClaims: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
