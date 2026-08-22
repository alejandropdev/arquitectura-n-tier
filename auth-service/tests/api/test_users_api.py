"""Pruebas del Requerimiento 9(c): autorización por propiedad en `/users/{id}`.

Estas pruebas son la evidencia central del entregable: demuestran que un
token de un usuario no opera sobre el recurso de otro (ownership) y que un
token emitido para otro servicio no sirve aquí (audience).
"""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.domain.entities import User
from app.infrastructure.persistence.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.security.hasher import Argon2PasswordHasher


def _register_and_login(client: TestClient, username: str) -> dict:
    payload = {"username": username, "email": f"{username}@example.com", "password": "Segura123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={
        "username": username, "password": payload["password"],
    })
    assert login.status_code == 200, login.text
    body = login.json()
    return {"token": body["access_token"], "id": body["user"]["id"], "username": username}


@pytest.fixture
def user_a(client: TestClient) -> dict:
    return _register_and_login(client, "usuario.a")


@pytest.fixture
def user_b(client: TestClient) -> dict:
    return _register_and_login(client, "usuario.b")


@pytest.fixture
def admin(client: TestClient, session_factory: sessionmaker[Session]) -> dict:
    session = session_factory()
    try:
        repo = SqlAlchemyUserRepository(session)
        password = "ClaveAdmin123"
        repo.add(User(
            username="admin.root", email="admin@example.com",
            password_hash=Argon2PasswordHasher().hash(password), role="admin",
        ))
        session.commit()
    finally:
        session.close()

    login = client.post("/api/v1/auth/login", json={"username": "admin.root", "password": password})
    assert login.status_code == 200, login.text
    body = login.json()
    return {"token": body["access_token"], "id": body["user"]["id"], "username": "admin.root"}


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_usuario_puede_leer_su_propio_perfil(client: TestClient, user_a: dict):
    response = client.get(f"/api/v1/users/{user_a['id']}", headers=_auth(user_a["token"]))

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == user_a["id"]
    assert body["role"] == "user"


def test_usuario_no_puede_leer_perfil_ajeno(client: TestClient, user_a: dict, user_b: dict):
    """Un token de un usuario no opera sobre el recurso de otro usuario."""
    response = client.get(f"/api/v1/users/{user_b['id']}", headers=_auth(user_a["token"]))

    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


def test_admin_puede_leer_cualquier_perfil(client: TestClient, user_a: dict, admin: dict):
    response = client.get(f"/api/v1/users/{user_a['id']}", headers=_auth(admin["token"]))

    assert response.status_code == 200
    assert response.json()["id"] == user_a["id"]


def test_sin_token_devuelve_401(client: TestClient, user_a: dict):
    response = client.get(f"/api/v1/users/{user_a['id']}")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def test_token_con_audience_incorrecta_devuelve_401(
    client: TestClient, user_a: dict, settings: Settings,
):
    """Un token de un servicio no sirve en otro: se firma con la misma clave
    pero para una audiencia distinta (`products-service`), y `auth-service`
    debe rechazarlo aunque la firma sea válida."""
    payload = {
        "sub": user_a["id"],
        "username": user_a["username"],
        "role": "user",
        "aud": ["products-service"],
        "iss": settings.jwt_issuer,
        "iat": 0,
        "exp": 9999999999,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    response = client.get(f"/api/v1/users/{user_a['id']}", headers=_auth(token))

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_audience"
