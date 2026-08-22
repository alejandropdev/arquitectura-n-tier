"""Cliente del Tier 2 (products-service), con las mismas tácticas de
disponibilidad que `AuthClient`.

* **Timeout**  : ninguna llamada queda colgada (prevención de fallas).
* **Retry**    : reintentos con backoff exponencial ante fallas transitorias —
                 solo cuando no hubo respuesta o la respuesta fue 5xx, es decir,
                 cuando otra instancia detrás del balanceador puede atender
                 (recuperación de fallas / redundancia activa). Solo se
                 reintentan métodos idempotentes (`GET`, `PATCH`, `DELETE`);
                 `POST` de creación no se reintenta para no duplicar recursos.
* **Breaker**  : si el servicio está caído se deja de insistir (prevención).

Un 4xx **nunca** se reintenta: es una decisión de negocio, no una falla.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import Settings
from app.core.exceptions import ProductApiError, ProductServiceUnavailable
from app.core.logging import audit, get_logger, request_id_var
from app.services.circuit_breaker import CircuitBreaker, CircuitOpenError

_logger = get_logger("services")

_IDEMPOTENT_METHODS = {"GET", "PATCH", "DELETE"}


class ProductsClient:
    def __init__(self, client: httpx.AsyncClient, settings: Settings,
                 breaker: CircuitBreaker | None = None) -> None:
        self._client = client
        self._settings = settings
        self._breaker = breaker or CircuitBreaker(
            failure_threshold=settings.breaker_failure_threshold,
            recovery_seconds=settings.breaker_recovery_seconds,
            name="products-service",
        )

    # --- Operaciones de negocio ---

    async def list_products(self, params: dict, *, actor: str | None = None) -> dict:
        return await self._request("GET", "/api/v1/products", params=params,
                                   action="web.products.list", actor=actor)

    async def get_product(self, product_id: str, *, actor: str | None = None) -> dict:
        return await self._request("GET", f"/api/v1/products/{product_id}",
                                   action="web.products.get", actor=actor)

    async def create_product(self, payload: dict, *, actor: str | None = None) -> dict:
        return await self._request("POST", "/api/v1/products", json=payload,
                                   action="web.products.create", actor=actor)

    async def update_product(self, product_id: str, payload: dict, *,
                             actor: str | None = None) -> dict:
        return await self._request("PATCH", f"/api/v1/products/{product_id}", json=payload,
                                   action="web.products.update", actor=actor)

    async def discontinue_product(self, product_id: str, *, actor: str | None = None) -> None:
        await self._request("DELETE", f"/api/v1/products/{product_id}",
                            action="web.products.discontinue", actor=actor)

    async def list_categories(self, *, actor: str | None = None) -> list[dict]:
        return await self._request("GET", "/api/v1/categories",
                                   action="web.categories.list", actor=actor)

    # --- Motor de llamadas resiliente ---

    async def _request(self, method: str, path: str, *, action: str,
                       params: dict | None = None, json: dict | None = None,
                       actor: str | None = None) -> dict | None:
        try:
            self._breaker.before_call()
        except CircuitOpenError as exc:
            audit(_logger, action, "FAILURE", component="ProductsClient", actor=actor,
                  message="Llamada cortada por el circuit breaker", level=logging.WARNING,
                  error_code="circuit_open")
            raise ProductServiceUnavailable() from exc

        attempts = max(1, self._settings.retry_attempts) if method in _IDEMPOTENT_METHODS else 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.request(
                    method, path, params=params, json=json,
                    timeout=self._settings.products_timeout_seconds,
                    headers={"X-Request-ID": request_id_var.get(),
                             "X-Actor": actor or "anonymous"},
                )
            except httpx.HTTPError as exc:
                # Sin respuesta: es seguro reintentar contra otra instancia.
                last_error = exc
                audit(_logger, action, "FAILURE", component="ProductsClient", actor=actor,
                      message=f"Intento {attempt}/{attempts} falló: {type(exc).__name__}",
                      level=logging.WARNING, error_code="transport_error", attempt=attempt)
                await self._backoff(attempt, attempts)
                continue

            if response.status_code >= 500:
                last_error = ProductServiceUnavailable()
                audit(_logger, action, "FAILURE", component="ProductsClient", actor=actor,
                      message=f"Intento {attempt}/{attempts} devolvió {response.status_code}",
                      level=logging.WARNING, error_code="upstream_5xx", attempt=attempt)
                await self._backoff(attempt, attempts)
                continue

            self._breaker.record_success()

            if response.status_code >= 400:
                raise self._api_error(response, action, actor)

            audit(_logger, action, "SUCCESS", component="ProductsClient", actor=actor,
                  message="Respuesta recibida del microservicio",
                  status=response.status_code, attempts=attempt)
            return response.json() if response.content else None

        self._breaker.record_failure()
        audit(_logger, action, "FAILURE", component="ProductsClient", actor=actor,
              message="Se agotaron los reintentos hacia el microservicio",
              level=logging.ERROR, error_code="retries_exhausted", attempts=attempts)
        raise ProductServiceUnavailable() from last_error

    async def _backoff(self, attempt: int, attempts: int) -> None:
        if attempt < attempts:
            await asyncio.sleep(self._settings.retry_backoff_seconds * (2 ** (attempt - 1)))

    def _api_error(self, response: httpx.Response, action: str,
                   actor: str | None) -> ProductApiError:
        try:
            body = response.json()
        except ValueError:
            body = {}
        error = ProductApiError(
            code=body.get("code", "products_api_error"),
            message=body.get("message", "No fue posible completar la operación"),
            status_code=response.status_code,
            detail=body if isinstance(body, dict) else {},
        )
        audit(_logger, action, "FAILURE", component="ProductsClient", actor=actor,
              message=error.message, level=logging.INFO,
              error_code=error.code, status=response.status_code)
        return error
