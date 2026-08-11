"""Observabilidad: logging estructurado en JSON.

Requisito del taller: **cada log debe incluir quién, cuándo y qué**.

    quién  -> campo `actor` (+ `client_ip`)
    cuándo -> campo `timestamp` (ISO-8601 UTC)
    qué    -> campos `action` + `outcome` (+ `detail`)

Adicionalmente se emite `request_id` para poder correlacionar el mismo caso de
uso a través de los tres tiers, y `tier`/`layer`/`component` para saber en qué
punto de la arquitectura ocurrió el evento.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# --- Contexto de la petición en curso (se llena en el middleware) ---
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
actor_var: ContextVar[str] = ContextVar("actor", default="anonymous")
client_ip_var: ContextVar[str] = ContextVar("client_ip", default="-")

# Campos que jamás deben aparecer en un log.
_REDACTED_KEYS = {"password", "current_password", "new_password", "token", "access_token",
                  "authorization", "password_hash"}

_SERVICE = {"service": "web", "tier": "presentacion", "instance": "local"}


class JsonFormatter(logging.Formatter):
    """Serializa cada registro como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            # CUÁNDO
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            # DÓNDE
            "service": _SERVICE["service"],
            "tier": _SERVICE["tier"],
            "instance": _SERVICE["instance"],
            "layer": getattr(record, "layer", record.name),
            "component": getattr(record, "component", record.module),
            # QUIÉN
            "actor": getattr(record, "actor", None) or actor_var.get(),
            "client_ip": getattr(record, "client_ip", None) or client_ip_var.get(),
            # QUÉ
            "action": getattr(record, "action", "log.message"),
            "outcome": getattr(record, "outcome", "INFO"),
            "message": record.getMessage(),
            # Correlación
            "request_id": getattr(record, "request_id", None) or request_id_var.get(),
        }

        for optional in ("duration_ms", "status_code", "error_type", "error_message"):
            value = getattr(record, optional, None)
            if value is not None:
                payload[optional] = value

        detail = getattr(record, "detail", None)
        if detail:
            payload["detail"] = _redact(detail)

        if record.exc_info:
            payload["stacktrace"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def _redact(data: dict[str, Any]) -> dict[str, Any]:
    """Nunca registramos credenciales ni tokens."""
    return {k: ("***" if k.lower() in _REDACTED_KEYS else v) for k, v in data.items()}


def configure_logging(level: str = "INFO", service: str | None = None,
                      tier: str | None = None, instance: str | None = None) -> None:
    """Instala el formateador JSON sobre stdout (los contenedores loguean a stdout)."""
    if service:
        _SERVICE["service"] = service
    if tier:
        _SERVICE["tier"] = tier
    if instance:
        _SERVICE["instance"] = instance

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Uvicorn ya loguea el acceso; nuestro middleware lo hace en formato estructurado.
    # httpx registra cada llamada saliente en INFO: demasiado ruido.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).handlers.clear()
        logging.getLogger(noisy).propagate = False


def get_logger(layer: str) -> logging.Logger:
    """Un logger por capa arquitectónica (api / application / domain / infrastructure)."""
    return logging.getLogger(layer)


def audit(logger: logging.Logger, action: str, outcome: str, *, message: str = "",
          actor: str | None = None, component: str = "", level: int = logging.INFO,
          exc_info: bool = False, **detail: Any) -> None:
    """Emite un evento auditable con la tripleta quién / cuándo / qué.

    `cuándo` lo agrega el formateador a partir del timestamp del registro.
    """
    logger.log(
        level,
        message or action,
        exc_info=exc_info,
        extra={
            "action": action,
            "outcome": outcome,
            "actor": actor or actor_var.get(),
            "request_id": request_id_var.get(),
            "layer": logger.name,
            "component": component or logger.name,
            "detail": detail or None,
        },
    )
