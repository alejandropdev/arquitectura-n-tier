"""Pruebas de integración del Tier 3: repositorio + unidad de trabajo reales."""

import uuid

import pytest

from app.domain.entities import User
from app.domain.exceptions import UserAlreadyExists
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def _user(username="ana", email="ana@example.com") -> User:
    return User(username=username, email=email, password_hash="hash::x")


def test_guarda_y_recupera_usuario(session_factory):
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        creado = uow.users.add(_user())
        uow.commit()

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        recuperado = uow.users.get_by_username("ana")

    assert recuperado is not None
    assert recuperado.id == creado.id
    assert recuperado.email == "ana@example.com"


def test_unicidad_de_username(session_factory):
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        uow.users.add(_user())
        uow.commit()

    with pytest.raises(UserAlreadyExists):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.users.add(_user(email="otra@example.com"))
            uow.commit()


def test_exists_detecta_el_campo_en_conflicto(session_factory):
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        uow.users.add(_user())
        uow.commit()

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.users.exists("ana", "nueva@example.com") == "username"
        assert uow.users.exists("otro", "ana@example.com") == "email"
        assert uow.users.exists("otro", "otro@example.com") is None


def test_rollback_deja_la_base_sin_cambios(session_factory):
    """Táctica de recuperación: si el caso de uso falla, no queda basura escrita."""
    with pytest.raises(RuntimeError):
        with SqlAlchemyUnitOfWork(session_factory) as uow:
            uow.users.add(_user())
            raise RuntimeError("falla simulada a mitad del caso de uso")

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.users.get_by_username("ana") is None


def test_actualiza_contadores_de_bloqueo(session_factory):
    from datetime import datetime, timedelta, timezone

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        user = uow.users.add(_user())
        uow.commit()

        user.failed_attempts = 3
        user.locked_until = datetime.now(timezone.utc) + timedelta(seconds=60)
        uow.users.update(user)
        uow.commit()

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        recuperado = uow.users.get_by_username("ana")

    assert recuperado.failed_attempts == 3
    assert recuperado.is_locked(datetime.now(timezone.utc))


def test_bitacora_de_intentos_de_login(session_factory):
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        uow.users.add(_user())
        uow.users.record_login_attempt("ana", False, "10.0.0.1", str(uuid.uuid4()),
                                       "password_incorrecta")
        uow.commit()

    from sqlalchemy import select

    from app.infrastructure.persistence.orm_models import LoginAttemptRow

    with session_factory() as session:
        registro = session.scalars(select(LoginAttemptRow)).one()

    assert registro.username == "ana"          # quién
    assert registro.occurred_at is not None    # cuándo
    assert registro.reason == "password_incorrecta"   # qué
    assert registro.successful is False


def test_get_by_id_devuelve_none_si_no_existe(session_factory):
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.users.get_by_id(uuid.uuid4()) is None
