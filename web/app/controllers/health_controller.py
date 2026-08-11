"""Sondas de salud del Tier 1 — detección de fallas.

`/health/ready` marca la instancia como no lista si el Tier 2 no responde, para
que el balanceador la saque de rotación en lugar de servir páginas rotas.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response, status

from app.core.config import get_settings
from app.core.logging import audit, get_logger

router = APIRouter(tags=["health"])
_logger = get_logger("controllers")


@router.get("/health")
async def liveness() -> dict:
    settings = get_settings()
    return {"status": "alive", "service": settings.service_name,
            "instance": settings.instance_id}


@router.get("/health/ready")
async def readiness(request: Request, response: Response) -> dict:
    settings = get_settings()
    ready = await request.app.state.auth_client.is_backend_ready()
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        audit(_logger, "health.ready", "FAILURE", component="health_controller",
              actor="system", level=logging.ERROR,
              message="Instancia web no lista: el microservicio no responde")
    return {
        "status": "ready" if ready else "not-ready",
        "service": settings.service_name,
        "instance": settings.instance_id,
        "dependencies": {"auth-service": "up" if ready else "down"},
    }
