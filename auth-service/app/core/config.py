"""Configuración del microservicio de autenticación (Tier 2).

Toda la configuración proviene de variables de entorno para que la misma imagen
Docker sirva en cualquier ambiente (12-factor).
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
