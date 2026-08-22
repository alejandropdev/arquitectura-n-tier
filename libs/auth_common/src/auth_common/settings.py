"""Configuración mínima que la librería necesita para firmar/validar tokens.

No lee variables de entorno por sí misma: cada servicio ya tiene su propio
objeto `Settings` (pydantic-settings) leyendo `JWT_SECRET`/`JWT_ALGORITHM`/
`JWT_ISSUER`; esta clase solo evita que la librería dependa de esas clases
concretas (acopladas a cada servicio) para permanecer reutilizable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthCommonSettings:
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth-service"
