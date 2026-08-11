"""Unidad de trabajo: una transacción por caso de uso.

Táctica de recuperación de fallas: **rollback**. Si algo falla a mitad del caso
de uso, la base de datos queda en el último estado consistente.
"""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import audit, get_logger
from app.infrastructure.exceptions import RepositoryError
from app.infrastructure.persistence.repositories.user_repository import (
    SqlAlchemyUserRepository,
)

_logger = get_logger("infrastructure")


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session: Session | None = None
        self.users: SqlAlchemyUserRepository | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None:
                self.rollback()
        finally:
            if self._session is not None:
                self._session.close()
            self._session = None
            self.users = None

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            audit(_logger, "uow.commit", "FAILURE", component="SqlAlchemyUnitOfWork",
                  message="No se pudo confirmar la transacción; se hizo rollback",
                  error_code="repository_error")
            raise RepositoryError("No se pudo confirmar la transacción", exc) from exc

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()
            audit(_logger, "uow.rollback", "SUCCESS", component="SqlAlchemyUnitOfWork",
                  message="Transacción revertida")
