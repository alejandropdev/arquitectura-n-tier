"""Tier 3 — conexión a la base de datos.

Decisiones ligadas a disponibilidad:

* `pool_pre_ping=True`  -> descarta conexiones muertas antes de usarlas
                           (prevención de fallas tras un reinicio de PostgreSQL).
* `pool_timeout`        -> evita que una petición quede colgada indefinidamente
                           esperando conexión (prevención de agotamiento).
* `connect_timeout`     -> falla rápido si el motor no responde.
"""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.infrastructure.exceptions import DatabaseUnavailable


def build_engine(settings: Settings) -> Engine:
    kwargs: dict = {"pool_pre_ping": True, "future": True}

    if settings.database_url.startswith("sqlite"):
        # Solo para pruebas locales / unitarias.
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout_seconds,
            pool_recycle=1800,
            connect_args={"connect_timeout": settings.db_connect_timeout_seconds},
        )

    return create_engine(settings.database_url, **kwargs)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def check_connection(engine: Engine) -> None:
    """Sonda de readiness: valida que el Tier 3 está accesible."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise DatabaseUnavailable("La base de datos no está disponible", exc) from exc
