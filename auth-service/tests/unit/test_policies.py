"""Pruebas unitarias de las reglas de dominio (sin BD, sin HTTP)."""

import pytest

from app.domain.exceptions import InvalidUsername, WeakPassword
from app.domain.policies import IdentityPolicy, PasswordPolicy


@pytest.fixture
def password_policy() -> PasswordPolicy:
    return PasswordPolicy(min_length=8)


def test_acepta_password_valida(password_policy):
    password_policy.validate("Segura123")


@pytest.mark.parametrize(
    "password, motivo",
    [
        ("Ab1", "al menos 8"),
        ("minusculas1", "mayúscula"),
        ("MAYUSCULAS1", "minúscula"),
        ("SinDigitos", "dígito"),
    ],
)
def test_rechaza_password_debil(password_policy, password, motivo):
    with pytest.raises(WeakPassword) as error:
        password_policy.validate(password)
    assert any(motivo in reason for reason in error.value.reasons)


def test_password_demasiado_larga():
    with pytest.raises(WeakPassword):
        PasswordPolicy(max_length=10).validate("A" * 11 + "a1")


@pytest.mark.parametrize("username", ["ana.perez", "user_1", "abc"])
def test_usuario_valido(username):
    IdentityPolicy().validate_username(username)


@pytest.mark.parametrize("username", ["ab", "con espacio", "a" * 33, "signo!"])
def test_usuario_invalido(username):
    with pytest.raises(InvalidUsername):
        IdentityPolicy().validate_username(username)


@pytest.mark.parametrize("email", ["ana@example.com", "a.b+c@sub.dominio.co"])
def test_email_valido(email):
    IdentityPolicy().validate_email(email)


@pytest.mark.parametrize("email", ["ana", "ana@", "@example.com", "ana@example"])
def test_email_invalido(email):
    with pytest.raises(InvalidUsername):
        IdentityPolicy().validate_email(email)
