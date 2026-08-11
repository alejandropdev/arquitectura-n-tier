"""Caso de uso: verificar un token de acceso (lo usa el Tier 1 en cada request protegida)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.ports import TokenProvider, UnitOfWork
from app.core.logging import audit, get_logger
from app.domain.exceptions import AccountInactive, DomainError, InvalidToken

_logger = get_logger("application")


@dataclass(frozen=True)
class VerifiedIdentity:
    user_id: UUID
    username: str
    email: str


class VerifyToken:
    def __init__(self, uow: UnitOfWork, tokens: TokenProvider) -> None:
        self._uow = uow
        self._tokens = tokens

    def execute(self, token: str) -> VerifiedIdentity:
        try:
            claims = self._tokens.decode(token)
            with self._uow as uow:
                user = uow.users.get_by_id(claims.user_id)
                if user is None:
                    raise InvalidToken("El usuario del token ya no existe")
                if not user.is_active:
                    raise AccountInactive()
                identity = VerifiedIdentity(user.id, user.username, user.email)
        except DomainError as exc:
            audit(_logger, "auth.verify_token", "FAILURE", component="VerifyToken",
                  message=exc.message, error_code=exc.code)
            raise

        audit(_logger, "auth.verify_token", "SUCCESS", actor=identity.username,
              component="VerifyToken", message="Token válido")
        return identity
