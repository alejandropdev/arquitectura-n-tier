"""Tier 2 — Microservicio de autenticación.

Punto de entrada: arma la aplicación, instala middlewares, manejadores de error
y enruta hacia la capa `api`.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.error_handlers import register_error_handlers
from app.api.routers import auth, health, users
from app.core.config import get_settings
from app.core.correlation import CorrelationMiddleware
from app.core.logging import audit, configure_logging, get_logger
from app.infrastructure.exceptions import DatabaseUnavailable
from app.infrastructure.persistence.database import (
    build_engine,
    build_session_factory,
    check_connection,
)
from app.infrastructure.persistence.orm_models import Base
from app.infrastructure.security.hasher import Argon2PasswordHasher

_logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = build_engine(settings)
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.hasher = Argon2PasswordHasher()

    # El esquema real lo crea `database/init/01-schema.sql`; esto solo cubre
    # ejecuciones locales/pruebas donde no hay script de inicialización.
    try:
        check_connection(engine)
        Base.metadata.create_all(engine)
        audit(_logger, "service.startup", "SUCCESS", component="main", actor="system",
              message="Microservicio de autenticación iniciado",
              instance=settings.instance_id)
    except DatabaseUnavailable:
        # Arrancamos igual: la sonda de readiness reportará 'not-ready' hasta que
        # PostgreSQL vuelva, en lugar de entrar en un ciclo de reinicios.
        audit(_logger, "service.startup", "FAILURE", component="main", actor="system",
              level=logging.ERROR,
              message="Arranque sin conexión a la base de datos; se reintentará por demanda")

    yield

    engine.dispose()
    audit(_logger, "service.shutdown", "SUCCESS", component="main", actor="system",
          message="Microservicio detenido")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.service_name, settings.tier,
                      settings.instance_id)

    app = FastAPI(
        title="Auth Service",
        description="Tier 2 — lógica de negocio de autenticación",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(CorrelationMiddleware)
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    return app


app = create_app()
