"""Sondas de salud (detección de fallas) y contrato de observabilidad."""

from __future__ import annotations

import json
import logging

from app.core.logging import JsonFormatter, audit, get_logger


def test_liveness(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_con_base_de_datos_disponible(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"]["database"] == "up"


def test_readiness_reporta_503_si_la_base_no_responde(client, monkeypatch):
    from app.infrastructure.exceptions import DatabaseUnavailable

    def falla(_engine):
        raise DatabaseUnavailable("simulada")

    monkeypatch.setattr("app.api.routers.health.check_connection", falla)

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not-ready"


# --------------------------- Observabilidad ---------------------------

def _formatear(record: logging.LogRecord) -> dict:
    return json.loads(JsonFormatter().format(record))


def test_todo_log_incluye_quien_cuando_y_que(caplog):
    logger = get_logger("application")
    with caplog.at_level(logging.INFO):
        audit(logger, "auth.login", "SUCCESS", actor="ana", component="Prueba",
              message="Autenticación exitosa")

    evento = _formatear(caplog.records[-1])

    assert evento["actor"] == "ana"           # QUIÉN
    assert evento["timestamp"]                # CUÁNDO
    assert evento["action"] == "auth.login"   # QUÉ
    assert evento["outcome"] == "SUCCESS"
    assert evento["layer"] == "application"
    assert "request_id" in evento


def test_los_logs_nunca_contienen_credenciales(caplog):
    logger = get_logger("application")
    with caplog.at_level(logging.INFO):
        audit(logger, "auth.login", "FAILURE", actor="ana", component="Prueba",
              password="SuperSecreta123", token="jwt-secreto")

    evento = _formatear(caplog.records[-1])

    assert evento["detail"]["password"] == "***"
    assert evento["detail"]["token"] == "***"
    assert "SuperSecreta123" not in json.dumps(evento)


def test_las_peticiones_http_quedan_trazadas(client, caplog):
    with caplog.at_level(logging.INFO):
        client.get("/health", headers={"X-Request-ID": "traza-123"})

    eventos = [_formatear(r) for r in caplog.records]
    http = [e for e in eventos if e["action"].startswith("http.")]

    assert http, "el middleware debe registrar cada petición"
    assert http[-1]["request_id"] == "traza-123"
    assert http[-1]["duration_ms"] >= 0
