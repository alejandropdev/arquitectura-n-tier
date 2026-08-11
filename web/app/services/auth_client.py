"""Cliente del Tier 2, con las tácticas de disponibilidad del lado del consumidor.

* **Timeout**  : ninguna llamada queda colgada (prevención de fallas).
* **Retry**    : reintentos con backoff exponencial ante fallas transitorias —
                 solo cuando no hubo respuesta o la respuesta fue 5xx, es decir,
                 cuando otra instancia detrás del balanceador puede atender
                 (recuperación de fallas / redundancia activa).
* **Breaker**  : si el servicio está caído se deja de insistir (prevención).

Un 4xx **nunca** se reintenta: es una decisión de negocio, no una falla.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import Settings
from app.core.exceptions import AuthApiError, AuthServiceUnavailable
from app.core.logging import audit, get_logger, request_id_var
from app.models.view_models import SessionUser
from app.services.circuit_breaker import CircuitBreaker, CircuitOpenError

_logger = get_logger("services")


class AuthClient:
    def __init__(self, client: httpx.AsyncClient, settings: Settings,
                 breaker: CircuitBreaker | None = None) -> None:
        self._client = client
        self._settings = settings
        self._breaker = breaker or CircuitBreaker(
            failure_threshold=settings.breaker_failure_threshold,
            recovery_seconds=settings.breaker_recovery_seconds,
        )

    # --- Operaciones de negocio ---

    async def register(self, username: str, email: str, password: str) -> dict:
        return await self._post(
            "/api/v1/auth/register",
            {"username": username, "email": email, "password": password},
            action="web.register", actor=username,
        )

    async def login(self, username: str, password: str) -> tuple[SessionUser, str]:
        data = await self._post(
            "/api/v1/auth/login",
            {"username": username, "password": password},
            action="web.login", actor=username,
        )
        user = SessionUser(
            id=data["user"]["id"],
            username=data["user"]["username"],
            email=data["user"]["email"],
            expires_at=data["expires_at"],
        )
        return user, data["access_token"]

    async def verify(self, token: str) -> SessionUser:
        data = await self._post("/api/v1/auth/verify", {"token": token},
                                action="web.verify_session")
        return SessionUser(id=data["user_id"], username=data["username"],
                           email=data["email"])

    async def is_backend_ready(self) -> bool:
        try:
            response = await self._client.get("/health/ready", timeout=2.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    # --- Motor de llamadas resiliente ---

    async def _post(self, path: str, payload: dict, *, action: str,
                    actor: str | None = None) -> dict:
        try:
            self._breaker.before_call()
        except CircuitOpenError as exc:
            audit(_logger, action, "FAILURE", component="AuthClient", actor=actor,
                  message="Llamada cortada por el circuit breaker", level=logging.WARNING,
                  error_code="circuit_open")
            raise AuthServiceUnavailable() from exc

        attempts = max(1, self._settings.retry_attempts)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = await self._client.post(
                    path, json=payload,
                    timeout=self._settings.auth_timeout_seconds,
                    headers={"X-Request-ID": request_id_var.get(),
                             "X-Actor": actor or "anonymous"},
                )
            except httpx.HTTPError as exc:
                # Sin respuesta: es seguro reintentar contra otra instancia.
                last_error = exc
                audit(_logger, action, "FAILURE", component="AuthClient", actor=actor,
                      message=f"Intento {attempt}/{attempts} falló: {type(exc).__name__}",
                      level=logging.WARNING, error_code="transport_error", attempt=attempt)
                await self._backoff(attempt, attempts)
                continue

            if response.status_code >= 500:
                last_error = AuthServiceUnavailable()
                audit(_logger, action, "FAILURE", component="AuthClient", actor=actor,
                      message=f"Intento {attempt}/{attempts} devolvió {response.status_code}",
                      level=logging.WARNING, error_code="upstream_5xx", attempt=attempt)
                await self._backoff(attempt, attempts)
                continue

            self._breaker.record_success()

            if response.status_code >= 400:
                raise self._api_error(response, action, actor)

            audit(_logger, action, "SUCCESS", component="AuthClient", actor=actor,
                  message="Respuesta recibida del microservicio",
                  status=response.status_code, attempts=attempt)
            return response.json()

        self._breaker.record_failure()
        audit(_logger, action, "FAILURE", component="AuthClient", actor=actor,
              message="Se agotaron los reintentos hacia el microservicio",
              level=logging.ERROR, error_code="retries_exhausted", attempts=attempts)
        raise AuthServiceUnavailable() from last_error

    async def _backoff(self, attempt: int, attempts: int) -> None:
        if attempt < attempts:
            await asyncio.sleep(self._settings.retry_backoff_seconds * (2 ** (attempt - 1)))

    def _api_error(self, response: httpx.Response, action: str,
                   actor: str | None) -> AuthApiError:
        try:
            body = response.json()
        except ValueError:
            body = {}
        error = AuthApiError(
            code=body.get("code", "auth_api_error"),
            message=body.get("message", "No fue posible completar la operación"),
            status_code=response.status_code,
            detail=body.get("detail") or {},
        )
        audit(_logger, action, "FAILURE", component="AuthClient", actor=actor,
              message=error.message, level=logging.INFO,
              error_code=error.code, status=response.status_code)
        return error
