"""Pruebas de las dependencias FastAPI sobre una app desechable: exigen
exactamente lo que el Requerimiento 9 pide demostrar — que un token de un
usuario no opera sobre otro y que el rol se respeta — y que el sobre de error
es el contrato uniforme {code, message, request_id, detail}.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from auth_common.fastapi_ext.dependencies import require_auth, require_owner_or_role, require_role
from auth_common.settings import AuthCommonSettings
from auth_common.tokens import encode_token

SECRET = "clave-de-pruebas"
SETTINGS = AuthCommonSettings(jwt_secret=SECRET)


def _token(role: str, sub: str = "user-1", audience: tuple[str, ...] = ("svc",)) -> str:
    token, _ = encode_token(
        subject=sub, username=sub, role=role, audience=audience,
        secret=SECRET, algorithm=SETTINGS.jwt_algorithm, issuer=SETTINGS.jwt_issuer,
        expires_in=timedelta(minutes=5),
    )
    return token


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    auth_dep = require_auth("svc", get_settings=lambda: SETTINGS)
    admin_dep = require_role("admin", require_auth_dep=auth_dep)
    owner_dep = require_owner_or_role("id", "admin", require_auth_dep=auth_dep)

    @app.get("/whoami")
    def whoami(claims=Depends(auth_dep)):
        return {"sub": claims.sub, "role": claims.role}

    @app.get("/admin-only")
    def admin_only(claims=Depends(admin_dep)):
        return {"sub": claims.sub}

    @app.get("/users/{id}")
    def get_user(id: str, claims=Depends(owner_dep)):
        return {"id": id}

    return TestClient(app)


def test_missing_token_returns_401_with_uniform_envelope(client: TestClient):
    response = client.get("/whoami")

    assert response.status_code == 401
    body = response.json()["detail"]
    assert body["code"] == "invalid_token"
    assert set(body) == {"code", "message", "request_id", "detail"}


def test_valid_token_returns_claims(client: TestClient):
    token = _token("user")

    response = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {"sub": "user-1", "role": "user"}


def test_wrong_audience_token_returns_401(client: TestClient):
    token = _token("user", audience=("otro-servicio",))

    response = client.get("/whoami", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_audience"


def test_role_check_rejects_non_admin(client: TestClient):
    token = _token("user")

    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"


def test_role_check_accepts_admin(client: TestClient):
    token = _token("admin")

    response = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_owner_check_accepts_self(client: TestClient):
    token = _token("user", sub="user-1")

    response = client.get("/users/user-1", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_owner_check_rejects_other_user(client: TestClient):
    """Un token de un usuario no opera sobre el recurso de otro usuario."""
    token = _token("user", sub="user-1")

    response = client.get("/users/user-2", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"


def test_owner_check_accepts_admin_on_other_user(client: TestClient):
    token = _token("admin", sub="admin-1")

    response = client.get("/users/user-2", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
