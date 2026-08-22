"""Configuración del microservicio de autenticación (Tier 2).

Toda la configuración proviene de variables de entorno para que la misma imagen
Docker sirva en cualquier ambiente (12-factor).
"""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Identidad del servicio (se emite en cada log) ---
    service_name: str = "auth-service"
    tier: str = "logica-de-negocio"
    instance_id: str = "auth-service-local"

    # --- Tier 3: base de datos ---
    database_url: str = "postgresql+psycopg://auth:auth@postgres:5432/authdb"
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_pool_timeout_seconds: int = 5
    db_connect_timeout_seconds: int = 3

    # --- Seguridad / tokens ---
    jwt_secret: str = "cambiame-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_issuer: str = "auth-service"
    # Servicios para los que se emite un token en login (Taller 2, Req. 9b):
    # el mismo token de sesión lo reenvía `web` tanto a este microservicio
    # como a `products-service` en nombre del usuario.
    # `NoDecode`: pydantic-settings intenta decodificar JSON por defecto
    # para tipos complejos leídos de variables de entorno, así que sin esto
    # rechazaría "auth-service,products-service" antes de llegar al
    # validador. Con `NoDecode` recibe el string crudo.
    jwt_audiences: Annotated[list[str], NoDecode] = ["auth-service", "products-service"]

    @field_validator("jwt_audiences", mode="before")
    @classmethod
    def _split_audiences(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    # --- Política de contraseñas ---
    password_min_length: int = 8
    password_max_length: int = 128

    # --- Política de bloqueo (prevención de fallas: fuerza bruta) ---
    max_failed_attempts: int = 5
    lockout_seconds: int = 300

    # --- Observabilidad ---
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Cacheado: la configuración se lee una sola vez por proceso."""
    return Settings()
