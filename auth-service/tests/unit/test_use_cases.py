"""Pruebas de los casos de uso con dobles de los puertos (sin BD, sin HTTP)."""

import pytest

from app.application.authenticate_user import AuthenticateUser, AuthenticateUserCommand
from app.application.register_user import RegisterUser, RegisterUserCommand
from app.application.verify_token import VerifyToken
from app.domain.exceptions import (
    AccountInactive,
    AccountLocked,
    InvalidCredentials,
    InvalidToken,
    InvalidUsername,
    UserAlreadyExists,
    WeakPassword,
)
from app.domain.policies import LockoutPolicy, PasswordPolicy
from tests.fakes import (
    FakeHasher,
    FakeTokenProvider,
    FakeUnitOfWork,
    FrozenClock,
    InMemoryUserRepository,
)


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork(InMemoryUserRepository())


@pytest.fixture
def clock() -> FrozenClock:
    return FrozenClock()


@pytest.fixture
def register(uow, clock) -> RegisterUser:
    return RegisterUser(uow, FakeHasher(), clock, PasswordPolicy(min_length=8))


@pytest.fixture
def tokens() -> FakeTokenProvider:
    return FakeTokenProvider()


@pytest.fixture
def authenticate(uow, clock, tokens) -> AuthenticateUser:
    return AuthenticateUser(uow, FakeHasher(), tokens, clock,
                            LockoutPolicy(max_attempts=3, lockout_seconds=60))


# --------------------------- Registro ---------------------------

def test_registro_exitoso(register, uow):
    user = register.execute(RegisterUserCommand("Ana.Perez", "ANA@Example.com", "Segura123"))

    assert user.username == "ana.perez"          # se normaliza a minúsculas
    assert user.email == "ana@example.com"
    assert user.password_hash == "hash::Segura123"
    assert uow.commits == 1


def test_registro_rechaza_usuario_duplicado(register, uow):
    register.execute(RegisterUserCommand("ana", "ana@example.com", "Segura123"))

    with pytest.raises(UserAlreadyExists):
        register.execute(RegisterUserCommand("ana", "otra@example.com", "Segura123"))
    assert uow.rollbacks == 1                     # la transacción se revierte


def test_registro_rechaza_password_debil(register):
    with pytest.raises(WeakPassword):
        register.execute(RegisterUserCommand("ana", "ana@example.com", "corta"))


def test_registro_rechaza_usuario_invalido(register):
    with pytest.raises(InvalidUsername):
        register.execute(RegisterUserCommand("a", "ana@example.com", "Segura123"))


# --------------------------- Login ---------------------------

def test_login_exitoso(register, authenticate):
    register.execute(RegisterUserCommand("ana", "ana@example.com", "Segura123"))

    session = authenticate.execute(AuthenticateUserCommand("ana", "Segura123"))

    assert session.username == "ana"
    assert session.access_token == "token::ana"


def test_login_con_usuario_inexistente(authenticate, uow):
    with pytest.raises(InvalidCredentials):
        authenticate.execute(AuthenticateUserCommand("nadie", "Segura123"))

    assert uow.users.attempts[-1] == ("nadie", False, "usuario_inexistente")


def test_login_con_password_incorrecta_incrementa_contador(register, authenticate, uow):
    register.execute(RegisterUserCommand("ana", "ana@example.com", "Segura123"))

    with pytest.raises(InvalidCredentials):
        authenticate.execute(AuthenticateUserCommand("ana", "Incorrecta1"))

    assert uow.users.get_by_username("ana").failed_attempts == 1


def test_bloqueo_tras_tres_intentos_fallidos(register, authenticate, clock, uow):
    register.execute(RegisterUserCommand("ana", "ana@example.com", "Segura123"))

    for _ in range(3):
        with pytest.raises(InvalidCredentials):
            authenticate.execute(AuthenticateUserCommand("ana", "Incorrecta1"))

    # El cuarto intento, incluso con la contraseña correcta, queda bloqueado.
    with pytest.raises(AccountLocked) as error:
        authenticate.execute(AuthenticateUserCommand("ana", "Segura123"))
    assert error.value.seconds_left == 60

    # Pasado el tiempo de bloqueo, vuelve a funcionar.
    clock.advance(61)
    session = authenticate.execute(AuthenticateUserCommand("ana", "Segura123"))
    assert session.username == "ana"
    assert uow.users.get_by_username("ana").failed_attempts == 0


def test_login_de_cuenta_inactiva(register, authenticate, uow):
    register.execute(RegisterUserCommand("ana", "ana@example.com", "Segura123"))
    uow.users.get_by_username("ana").is_active = False

    with pytest.raises(AccountInactive):
        authenticate.execute(AuthenticateUserCommand("ana", "Segura123"))


# --------------------------- Verificación de token ---------------------------

def test_verificacion_de_token_valido(register, authenticate, tokens, uow):
    register.execute(RegisterUserCommand("ana", "ana@example.com", "Segura123"))
    session = authenticate.execute(AuthenticateUserCommand("ana", "Segura123"))

    identity = VerifyToken(uow, tokens).execute(session.access_token)

    assert identity.username == "ana"


def test_verificacion_de_token_invalido(uow, tokens):
    with pytest.raises(InvalidToken):
        VerifyToken(uow, tokens).execute("token-falso")
