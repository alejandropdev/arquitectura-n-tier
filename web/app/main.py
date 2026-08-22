"""Tier 1 — Aplicación web (patrón MVC sobre FastAPI + Jinja2)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.controllers import (
    auth_controller,
    health_controller,
    home_controller,
    products_controller,
)
from app.core.config import get_settings
from app.core.correlation import CorrelationMiddleware
from app.core.exceptions import AuthServiceUnavailable, PresentationError, ProductServiceUnavailable
from app.core.logging import audit, configure_logging, get_logger
from app.services.auth_client import AuthClient
from app.services.circuit_breaker import CircuitBreaker
from app.services.products_client import ProductsClient
from app.views.renderer import templates

_logger = get_logger("controllers")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Cliente HTTP reutilizado: pool de conexiones + límites explícitos.
    http_client = httpx.AsyncClient(
        base_url=settings.auth_service_url,
        timeout=httpx.Timeout(settings.auth_timeout_seconds),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    app.state.http_client = http_client
    app.state.auth_client = AuthClient(
        http_client,
        settings,
        CircuitBreaker(
            failure_threshold=settings.breaker_failure_threshold,
            recovery_seconds=settings.breaker_recovery_seconds,
        ),
    )

    products_http_client = httpx.AsyncClient(
        base_url=settings.products_service_url,
        timeout=httpx.Timeout(settings.products_timeout_seconds),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    app.state.products_http_client = products_http_client
    app.state.products_client = ProductsClient(
        products_http_client,
        settings,
        CircuitBreaker(
            failure_threshold=settings.breaker_failure_threshold,
            recovery_seconds=settings.breaker_recovery_seconds,
            name="products-service",
        ),
    )

    audit(_logger, "service.startup", "SUCCESS", component="main", actor="system",
          message="Aplicación web iniciada", instance=settings.instance_id,
          backend=settings.auth_service_url)

    yield

    await http_client.aclose()
    await products_http_client.aclose()
    audit(_logger, "service.shutdown", "SUCCESS", component="main", actor="system",
          message="Aplicación web detenida")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.service_name, settings.tier,
                      settings.instance_id)

    app = FastAPI(title="Portal de Autenticación", version="1.0.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None)
    app.add_middleware(CorrelationMiddleware)
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")),
              name="static")

    app.include_router(home_controller.router)
    app.include_router(health_controller.router)
    app.include_router(auth_controller.router)
    app.include_router(products_controller.router)

    _register_error_handlers(app)
    return app


def _register_error_handlers(app: FastAPI) -> None:
    """Ninguna excepción llega al navegador como stacktrace."""

    @app.exception_handler(AuthServiceUnavailable)
    async def _unavailable(request: Request, exc: AuthServiceUnavailable) -> HTMLResponse:
        audit(_logger, "web.error", "FAILURE", component="main", message=exc.message,
              level=logging.ERROR, error_code=exc.code, path=request.url.path)
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "Servicio no disponible", "message": exc.message, "status_code": 503},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @app.exception_handler(ProductServiceUnavailable)
    async def _products_unavailable(request: Request,
                                     exc: ProductServiceUnavailable) -> HTMLResponse:
        audit(_logger, "web.error", "FAILURE", component="main", message=exc.message,
              level=logging.ERROR, error_code=exc.code, path=request.url.path)
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "Servicio no disponible", "message": exc.message, "status_code": 503},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @app.exception_handler(PresentationError)
    async def _presentation(request: Request, exc: PresentationError) -> HTMLResponse:
        audit(_logger, "web.error", "FAILURE", component="main", message=exc.message,
              level=logging.WARNING, error_code=exc.code, path=request.url.path)
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "No se pudo completar la operación", "message": exc.message,
             "status_code": 400},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> HTMLResponse:
        audit(_logger, "web.error", "FAILURE", component="main",
              message="Excepción no controlada en la capa de presentación",
              level=logging.CRITICAL, exc_info=True, error_code=type(exc).__name__,
              path=request.url.path)
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "Error inesperado",
             "message": "Ocurrió un error inesperado. El incidente quedó registrado.",
             "status_code": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


app = create_app()
