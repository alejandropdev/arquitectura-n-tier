"""Fixtures compartidas de las pruebas del microservicio.

Las pruebas usan SQLite en un archivo temporal: el repositorio es el mismo
código que corre contra PostgreSQL (SQLAlchemy), así que la capa de datos se
ejercita de verdad sin necesitar un contenedor.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.infrastructure.persistence.database import build_engine, build_session_factory
from app.infrastructure.persistence.orm_models import Base


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path}/test.db",
        jwt_secret="clave-de-pruebas",
        jwt_expiration_minutes=5,
        max_failed_attempts=3,
        lockout_seconds=300,
        instance_id="auth-service-test",
    )


@pytest.fixture
def session_factory(settings: Settings) -> sessionmaker[Session]:
    engine = build_engine(settings)
    Base.metadata.create_all(engine)
    return build_session_factory(engine)


@pytest.fixture
def client(settings: Settings, monkeypatch) -> TestClient:
    """Aplicación real completa (middlewares + handlers) sobre la BD de pruebas."""
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    get_settings.cache_clear()

    import app.main as main_module

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr("app.api.dependencies.get_settings", lambda: settings)
    monkeypatch.setattr("app.api.routers.health.get_settings", lambda: settings)

    application = main_module.create_app()
    application.dependency_overrides[get_settings] = lambda: settings

    with TestClient(application, raise_server_exceptions=False) as test_client:
        yield test_client

    get_settings.cache_clear()


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    payload = {"username": "ana.perez", "email": "ana@example.com", "password": "Segura123"}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload
