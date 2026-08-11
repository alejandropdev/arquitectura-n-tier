"""Reglas de bloqueo de cuenta en la entidad User (reloj inyectado, sin sleep)."""

from datetime import datetime, timedelta, timezone

from app.domain.entities import User


def _user() -> User:
    return User(username="ana", email="ana@example.com", password_hash="x")


def test_no_bloquea_antes_del_umbral():
    now = datetime.now(timezone.utc)
    user = _user()

    for _ in range(2):
        user.register_failed_attempt(now, max_attempts=3, lockout_seconds=300)

    assert user.failed_attempts == 2
    assert not user.is_locked(now)


def test_bloquea_al_alcanzar_el_umbral():
    now = datetime.now(timezone.utc)
    user = _user()

    for _ in range(3):
        user.register_failed_attempt(now, max_attempts=3, lockout_seconds=300)

    assert user.is_locked(now)
    assert user.seconds_locked(now) == 300


def test_el_bloqueo_expira_con_el_tiempo():
    now = datetime.now(timezone.utc)
    user = _user()
    for _ in range(3):
        user.register_failed_attempt(now, max_attempts=3, lockout_seconds=60)

    despues = now + timedelta(seconds=61)
    assert not user.is_locked(despues)
    assert user.seconds_locked(despues) == 0


def test_login_exitoso_reinicia_contadores():
    now = datetime.now(timezone.utc)
    user = _user()
    for _ in range(3):
        user.register_failed_attempt(now, max_attempts=3, lockout_seconds=60)

    user.register_successful_login(now)

    assert user.failed_attempts == 0
    assert user.locked_until is None
    assert user.last_login_at == now
