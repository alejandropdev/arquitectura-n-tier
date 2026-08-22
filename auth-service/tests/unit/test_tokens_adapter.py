"""Pruebas del adaptador `JwtTokenProvider` sobre `auth_common`: confirma que
`issue()` emite `role`/`aud` correctamente (Requerimiento 9a)."""

from __future__ import annotations

import uuid

import jwt

from app.domain.entities import User
from app.infrastructure.security.jwt_provider import JwtTokenProvider

SECRET = "clave-de-pruebas"


def _provider(**overrides) -> JwtTokenProvider:
    params = dict(
        secret=SECRET, algorithm="HS256", expiration_minutes=5, issuer="auth-service",
        audiences=["auth-service", "products-service"],
    )
    params.update(overrides)
    return JwtTokenProvider(**params)


def test_issue_sets_role_and_audience():
    user = User(
        id=uuid.uuid4(), username="ana", email="ana@example.com",
        password_hash="hash", role="admin",
    )
    provider = _provider()

    token, expires_at = provider.issue(user)

    payload = jwt.decode(token, SECRET, algorithms=["HS256"], issuer="auth-service",
                         audience="auth-service")
    assert payload["sub"] == str(user.id)
    assert payload["role"] == "admin"
    assert set(payload["aud"]) == {"auth-service", "products-service"}
    assert payload["exp"] == int(expires_at.timestamp())


def test_decode_does_not_enforce_audience():
    """`/verify` (usado por `web`) no exige audiencia: valida la sesión,
    no es en sí mismo un resource server."""
    user = User(
        id=uuid.uuid4(), username="ana", email="ana@example.com",
        password_hash="hash", role="user",
    )
    provider = _provider(audiences=["products-service"])
    token, _ = provider.issue(user)

    claims = provider.decode(token)

    assert claims.user_id == user.id
    assert claims.username == user.username
