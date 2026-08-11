"""Excepciones de la capa de infraestructura (Tier 3 y adaptadores).

Regla de traducción de errores: ningún error del driver de base de datos ni de
una librería externa escapa hacia arriba tal cual; se envuelve aquí y la capa
`api` decide el código HTTP.
"""

from __future__ import annotations


class InfrastructureError(Exception):
    code = "infrastructure_error"

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


class RepositoryError(InfrastructureError):
    """Falla al leer/escribir en el repositorio de datos."""

    code = "repository_error"


class DatabaseUnavailable(InfrastructureError):
    """La base de datos no responde: el servicio queda 'not ready' (503)."""

    code = "database_unavailable"
