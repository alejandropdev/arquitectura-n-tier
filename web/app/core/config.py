"""Configuración del Tier 1 (presentación)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "web"
    tier: str = "presentacion"
    instance_id: str = "web-local"

    # --- Tier 2 ---
    auth_service_url: str = "http://gateway:8081"
    auth_timeout_seconds: float = 3.0

    # --- Seguridad / tokens (Taller 2, Requerimiento 9) ---
    # Mismas variables que usa auth-service: `web` no valida sesión con
    # esto (eso lo sigue haciendo /verify), solo decodifica localmente para
    # leer `role` y mostrarlo en la vista — ver `controllers/dependencies.py`.
    jwt_secret: str = "cambiame-en-produccion"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "auth-service"

    # --- Táctica de recuperación: reintentos con backoff ---
    retry_attempts: int = 3
    retry_backoff_seconds: float = 0.2

    # --- Táctica de prevención: circuit breaker ---
    breaker_failure_threshold: int = 5
    breaker_recovery_seconds: float = 15.0

    # --- Sesión ---
    session_cookie: str = "auth_session"
    cookie_secure: bool = False  # True detrás de HTTPS

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
