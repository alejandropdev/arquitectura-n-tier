"""Fixtures del Tier 1.

El Tier 2 se reemplaza por un doble: la presentación se prueba de forma aislada,
que es justamente lo que permite la separación en tiers.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AuthApiError, AuthServiceUnavailable
from app.models.view_models import SessionUser


class StubAuthClient:
    """Doble del cliente del microservicio."""

    def __init__(self) -> None:
        self.usuarios: dict[str, str] = {}
        self.tokens: dict[str, SessionUser] = {}
        self.caido = False
        self.backend_ready = True
        self.llamadas: list[str] = []

    async def register(self, username: str, email: str, password: str) -> dict:
        self.llamadas.append("register")
        self._verificar_disponibilidad()
        if username in self.usuarios:
            raise AuthApiError("user_already_exists", "Ya existe un usuario con ese username",
                               409)
        self.usuarios[username] = password
        return {"id": "id-1", "username": username, "email": email}

    async def login(self, username: str, password: str) -> tuple[SessionUser, str]:
        self.llamadas.append("login")
        self._verificar_disponibilidad()
        if self.usuarios.get(username) != password:
            raise AuthApiError("invalid_credentials", "Usuario o contraseña incorrectos", 401)
        user = SessionUser(id="id-1", username=username, email=f"{username}@example.com")
        token = f"token::{username}"
        self.tokens[token] = user
        return user, token

    async def verify(self, token: str) -> SessionUser:
        self.llamadas.append("verify")
        self._verificar_disponibilidad()
        if token not in self.tokens:
            raise AuthApiError("invalid_token", "Token inválido o expirado", 401)
        return self.tokens[token]

    async def is_backend_ready(self) -> bool:
        return self.backend_ready and not self.caido

    def _verificar_disponibilidad(self) -> None:
        if self.caido:
            raise AuthServiceUnavailable()


@pytest.fixture
def stub() -> StubAuthClient:
    return StubAuthClient()


@pytest.fixture
def client(stub: StubAuthClient) -> TestClient:
    from app.main import create_app

    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        test_client.app.state.auth_client = stub   # se sustituye el Tier 2
        yield test_client


@pytest.fixture
def usuario_registrado(stub: StubAuthClient) -> dict:
    stub.usuarios["ana.perez"] = "Segura123"
    return {"username": "ana.perez", "password": "Segura123"}
