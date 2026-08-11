"""Sondas de salud — táctica de **detección de fallas** (ping/echo + monitor).

* `/health`        liveness: el proceso responde. Lo usa Docker para reiniciar.
* `/health/ready`  readiness: además el Tier 3 está accesible. Lo usa nginx/el
                   operador para decidir si esta instancia debe recibir tráfico.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response, status

from app.api.schemas import HealthResponse
from app.core.config import get_settings
from app.core.logging import audit, get_logger
from app.infrastructure.exceptions import DatabaseUnavailable
from app.infrastructure.persistence.database import check_connection

router = APIRouter(tags=["health"])
_logger = get_logger("api")


@router.get("/health", response_model=HealthResponse)
def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="alive", service=settings.service_name,
                          instance=settings.instance_id)


@router.get("/health/ready", response_model=HealthResponse)
def readiness(request: Request, response: Response) -> HealthResponse:
    settings = get_settings()
    try:
        check_connection(request.app.state.engine)
    except DatabaseUnavailable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        audit(_logger, "health.ready", "FAILURE", component="health",
              message="La instancia no está lista: base de datos inaccesible",
              level=logging.ERROR, actor="system")
        return HealthResponse(status="not-ready", service=settings.service_name,
                              instance=settings.instance_id,
                              dependencies={"database": "down"})

    return HealthResponse(status="ready", service=settings.service_name,
                          instance=settings.instance_id,
                          dependencies={"database": "up"})
