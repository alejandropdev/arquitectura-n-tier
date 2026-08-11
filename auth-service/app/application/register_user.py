"""Caso de uso: registrar un usuario."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import Clock, PasswordHasher, UnitOfWork
from app.core.logging import audit, get_logger
from app.domain.entities import User
from app.domain.exceptions import DomainError, UserAlreadyExists
from app.domain.policies import IdentityPolicy, PasswordPolicy

_logger = get_logger("application")


@dataclass(frozen=True)
class RegisterUserCommand:
    username: str
    email: str
    password: str


class RegisterUser:
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, clock: Clock,
                 password_policy: PasswordPolicy,
                 identity_policy: IdentityPolicy | None = None) -> None:
        self._uow = uow
        self._hasher = hasher
        self._clock = clock
        self._password_policy = password_policy
        self._identity_policy = identity_policy or IdentityPolicy()

    def execute(self, command: RegisterUserCommand) -> User:
        username = command.username.strip().lower()
        email = command.email.strip().lower()

        try:
            # 1) Reglas de dominio (prevención de excepciones aguas abajo).
            self._identity_policy.validate_username(username)
            self._identity_policy.validate_email(email)
            self._password_policy.validate(command.password)

            # 2) Persistencia dentro de una transacción.
            with self._uow as uow:
                conflict = uow.users.exists(username, email)
                if conflict:
                    raise UserAlreadyExists(conflict)

                user = uow.users.add(
                    User(
                        username=username,
                        email=email,
                        password_hash=self._hasher.hash(command.password),
                        created_at=self._clock.now(),
                    )
                )
                uow.commit()
        except DomainError as exc:
            audit(_logger, "auth.register", "FAILURE", actor=username,
                  component="RegisterUser", message=exc.message,
                  error_code=exc.code)
            raise

        audit(_logger, "auth.register", "SUCCESS", actor=username,
              component="RegisterUser", message="Usuario registrado",
              user_id=str(user.id))
        return user
