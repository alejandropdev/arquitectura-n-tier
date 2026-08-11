"""Tier 3 — repositorio de usuarios (implementa el puerto `UserRepository`).

Es el **único** componente que conoce SQL/ORM. Traduce los errores del driver a
excepciones propias para que las capas superiores nunca vean `SQLAlchemyError`.
"""

from __future__ import annotations

import uuid
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.logging import audit, get_logger
from app.domain.entities import User
from app.domain.exceptions import UserAlreadyExists
from app.infrastructure.exceptions import DatabaseUnavailable, RepositoryError
from app.infrastructure.persistence.mappers import row_to_user, user_to_row
from app.infrastructure.persistence.orm_models import LoginAttemptRow, UserRow

_logger = get_logger("infrastructure")


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # --- Lecturas ---

    def get_by_username(self, username: str) -> User | None:
        row = self._one(select(UserRow).where(UserRow.username == username),
                        "users.get_by_username", username)
        return row_to_user(row) if row else None

    def get_by_id(self, user_id: UUID) -> User | None:
        row = self._one(select(UserRow).where(UserRow.id == user_id),
                        "users.get_by_id", str(user_id))
        return row_to_user(row) if row else None

    def exists(self, username: str, email: str) -> str | None:
        row = self._one(
            select(UserRow).where(or_(UserRow.username == username, UserRow.email == email)),
            "users.exists", username,
        )
        if row is None:
            return None
        return "username" if row.username == username else "email"

    # --- Escrituras ---

    def add(self, user: User) -> User:
        row = user_to_row(user)
        try:
            self._session.add(row)
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            audit(_logger, "users.add", "FAILURE", component="SqlAlchemyUserRepository",
                  message="Violación de unicidad al insertar el usuario",
                  actor=user.username, error_code="integrity_error")
            raise UserAlreadyExists("username") from exc
        except OperationalError as exc:
            raise self._unavailable("users.add", exc) from exc
        except SQLAlchemyError as exc:
            raise self._failed("users.add", exc) from exc

        audit(_logger, "users.add", "SUCCESS", component="SqlAlchemyUserRepository",
              message="Usuario insertado", actor=user.username, user_id=str(row.id))
        return row_to_user(row)

    def update(self, user: User) -> None:
        try:
            row = self._session.get(UserRow, user.id)
            if row is None:
                raise RepositoryError("El usuario a actualizar no existe")
            row.failed_attempts = user.failed_attempts
            row.locked_until = user.locked_until
            row.last_login_at = user.last_login_at
            row.is_active = user.is_active
            self._session.flush()
        except OperationalError as exc:
            raise self._unavailable("users.update", exc) from exc
        except SQLAlchemyError as exc:
            raise self._failed("users.update", exc) from exc

    def record_login_attempt(self, username: str, successful: bool, client_ip: str,
                             request_id: str, reason: str | None = None) -> None:
        try:
            user_row = self._session.scalars(
                select(UserRow).where(UserRow.username == username)
            ).first()
            self._session.add(
                LoginAttemptRow(
                    id=uuid.uuid4(),
                    username=username,
                    successful=successful,
                    reason=reason,
                    client_ip=client_ip,
                    request_id=request_id,
                    user_id=user_row.id if user_row else None,
                )
            )
            self._session.flush()
        except OperationalError as exc:
            raise self._unavailable("users.record_login_attempt", exc) from exc
        except SQLAlchemyError as exc:
            raise self._failed("users.record_login_attempt", exc) from exc

    # --- Utilidades internas ---

    def _one(self, statement, action: str, actor: str) -> UserRow | None:
        try:
            return self._session.scalars(statement).first()
        except OperationalError as exc:
            raise self._unavailable(action, exc, actor) from exc
        except SQLAlchemyError as exc:
            raise self._failed(action, exc, actor) from exc

    def _unavailable(self, action: str, exc: Exception,
                     actor: str | None = None) -> DatabaseUnavailable:
        audit(_logger, action, "FAILURE", component="SqlAlchemyUserRepository", actor=actor,
              message="La base de datos no respondió", error_code="database_unavailable")
        return DatabaseUnavailable("La base de datos no está disponible", exc)

    def _failed(self, action: str, exc: Exception,
                actor: str | None = None) -> RepositoryError:
        audit(_logger, action, "FAILURE", component="SqlAlchemyUserRepository", actor=actor,
              message=f"Error de persistencia: {type(exc).__name__}",
              error_code="repository_error")
        return RepositoryError("Error al acceder al repositorio de usuarios", exc)
