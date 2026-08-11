"""Middleware de correlación y traza de peticiones.

Propaga `X-Request-ID` entre tiers: el Tier 1 lo genera, nginx lo reenvía y el
Tier 2 lo reutiliza. Así una misma operación de negocio se puede seguir por los
logs de todos los contenedores.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import actor_var, client_ip_var, get_logger, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
ACTOR_HEADER = "X-Actor"

_logger = get_logger("api")


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request_id_var.set(request_id)
        actor_var.set(request.headers.get(ACTOR_HEADER) or "anonymous")
        client_ip_var.set(_client_ip(request))
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # el handler global ya respondió; aquí solo trazamos
            _log(request, "FAILURE", None, started, error=exc)
            raise

        _log(request, "SUCCESS" if response.status_code < 400 else "FAILURE",
             response.status_code, started)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "-"


def _log(request: Request, outcome: str, status_code: int | None, started: float,
         error: Exception | None = None) -> None:
    _logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "action": f"http.{request.method.lower()}{request.url.path}",
            "outcome": outcome,
            "layer": "api",
            "component": "CorrelationMiddleware",
            "request_id": request_id_var.get(),
            "status_code": status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            "error_type": type(error).__name__ if error else None,
            "error_message": str(error) if error else None,
            "detail": None,
        },
    )
