"""Caso de uso: autenticar un usuario (login)."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import Clock, PasswordHasher, TokenProvider, UnitOfWork
from app.core.logging import audit, get_logger, request_id_var
from app.domain.entities import AuthenticatedSession
from app.domain.exceptions import (
    AccountInactive,
    AccountLocked,
    DomainError,
    InvalidCredentials,
)
from app.domain.policies import LockoutPolicy

_logger = get_logger("application")


@dataclass(frozen=True)
class AuthenticateUserCommand:
    username: str
    password: str
    client_ip: str = "-"


class AuthenticateUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, tokens: TokenProvider,
                 clock: Clock, lockout: LockoutPolicy) -> None:
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock
        self._lockout = lockout

    def execute(self, command: AuthenticateUserCommand) -> AuthenticatedSession:
        username = command.username.strip().lower()
        now = self._clock.now()

        try:
            with self._uow as uow:
                user = uow.users.get_by_username(username)

                # Usuario inexistente: mensaje genérico para no filtrar qué cuentas existen.
                if user is None:
                    self._deny(uow, username, command.client_ip, "usuario_inexistente")
                    raise InvalidCredentials()

                if user.is_locked(now):
                    seconds = user.seconds_locked(now)
                    self._deny(uow, username, command.client_ip, "cuenta_bloqueada")
                    raise AccountLocked(seconds)

                if not user.is_active:
                    self._deny(uow, username, command.client_ip, "cuenta_inactiva")
                    raise AccountInactive()

                if not self._hasher.verify(command.password, user.password_hash):
                    user.register_failed_attempt(
                        now, self._lockout.max_attempts, self._lockout.lockout_seconds
                    )
                    uow.users.update(user)
                    self._deny(uow, username, command.client_ip, "password_incorrecta")
                    raise InvalidCredentials()

                # Éxito: se reinicia el contador de fallos y se emite el token.
                user.register_successful_login(now)
                uow.users.update(user)
                token, expires_at = self._tokens.issue(user)
                uow.users.record_login_attempt(
                    username, True, command.client_ip, request_id_var.get()
                )
                uow.commit()

                session = AuthenticatedSession(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    access_token=token,
                    expires_at=expires_at,
                )
        except DomainError as exc:
            audit(_logger, "auth.login", "FAILURE", actor=username,
                  component="AuthenticateUser", message=exc.message, error_code=exc.code,
                  client_ip=command.client_ip)
            raise

        audit(_logger, "auth.login", "SUCCESS", actor=username, component="AuthenticateUser",
              message="Autenticación exitosa", user_id=str(session.user_id),
              client_ip=command.client_ip)
        return session

    def _deny(self, uow: UnitOfWork, username: str, client_ip: str, reason: str) -> None:
        """Registra el intento fallido en la bitácora y consolida la transacción.

        Se hace commit aquí para que el contador de bloqueo no se pierda al
        propagar la excepción (el `__exit__` del UoW hace rollback).
        """
        uow.users.record_login_attempt(
            username, False, client_ip, request_id_var.get(), reason
        )
        uow.commit()
