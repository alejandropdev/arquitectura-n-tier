"""Dobles de prueba de los puertos: permiten probar los casos de uso sin BD.

Que esto sea posible es la evidencia de que la capa de aplicación depende de
abstracciones y no de la infraestructura.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.domain.entities import TokenClaims, User
from app.domain.exceptions import InvalidToken


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.attempts: list[tuple[str, bool, str | None]] = []

    def get_by_username(self, username: str) -> User | None:
        return self.users.get(username)

    def get_by_id(self, user_id) -> User | None:
        return next((u for u in self.users.values() if u.id == user_id), None)

    def exists(self, username: str, email: str) -> str | None:
        if username in self.users:
            return "username"
        if any(u.email == email for u in self.users.values()):
            return "email"
        return None

    def add(self, user: User) -> User:
        user.id = user.id or uuid.uuid4()
        self.users[user.username] = user
        return user

    def update(self, user: User) -> None:
        self.users[user.username] = user

    def record_login_attempt(self, username, successful, client_ip, request_id, reason=None):
        self.attempts.append((username, successful, reason))


class FakeUnitOfWork:
    def __init__(self, repository: InMemoryUserRepository | None = None) -> None:
        self.users = repository or InMemoryUserRepository()
        self.commits = 0
        self.rollbacks = 0

    def __enter__(self) -> "FakeUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeHasher:
    """Hash reversible y trivial: las pruebas no necesitan criptografía real."""

    def hash(self, plain: str) -> str:
        return f"hash::{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hash::{plain}"


class FakeTokenProvider:
    def __init__(self) -> None:
        self.issued: dict[str, User] = {}

    def issue(self, user: User) -> tuple[str, datetime]:
        token = f"token::{user.username}"
        self.issued[token] = user
        return token, datetime.now(timezone.utc)

    def decode(self, token: str) -> TokenClaims:
        user = self.issued.get(token)
        if user is None:
            raise InvalidToken()
        return TokenClaims(user_id=user.id, username=user.username,
                           expires_at=datetime.now(timezone.utc))


class FrozenClock:
    def __init__(self, moment: datetime | None = None) -> None:
        self.moment = moment or datetime.now(timezone.utc)

    def now(self) -> datetime:
        return self.moment

    def advance(self, seconds: float) -> None:
        from datetime import timedelta

        self.moment = self.moment + timedelta(seconds=seconds)
