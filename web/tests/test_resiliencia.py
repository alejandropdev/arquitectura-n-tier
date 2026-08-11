"""Pruebas de las tácticas de disponibilidad del Tier 1: retry y circuit breaker."""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import AuthApiError, AuthServiceUnavailable
from app.services.auth_client import AuthClient
from app.services.circuit_breaker import CircuitBreaker, CircuitOpenError, State


# --------------------------- Circuit breaker ---------------------------

class RelojFalso:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def avanzar(self, segundos: float) -> None:
        self.t += segundos


@pytest.fixture
def reloj() -> RelojFalso:
    return RelojFalso()


@pytest.fixture
def breaker(reloj) -> CircuitBreaker:
    return CircuitBreaker(failure_threshold=3, recovery_seconds=10, time_source=reloj)


def test_el_circuito_empieza_cerrado(breaker):
    assert breaker.state is State.CLOSED
    breaker.before_call()


def test_se_abre_tras_el_umbral_de_fallas(breaker):
    for _ in range(3):
        breaker.record_failure()

    assert breaker.state is State.OPEN
    with pytest.raises(CircuitOpenError):
        breaker.before_call()


def test_los_exitos_reinician_el_contador(breaker):
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_success()
    breaker.record_failure()
    breaker.record_failure()

    assert breaker.state is State.CLOSED


def test_pasa_a_semiabierto_tras_la_ventana_de_recuperacion(breaker, reloj):
    for _ in range(3):
        breaker.record_failure()
    reloj.avanzar(10)

    assert breaker.state is State.HALF_OPEN
    breaker.before_call()          # se permite una llamada de prueba


def test_semiabierto_se_cierra_si_la_prueba_tiene_exito(breaker, reloj):
    for _ in range(3):
        breaker.record_failure()
    reloj.avanzar(10)
    assert breaker.state is State.HALF_OPEN

    breaker.record_success()

    assert breaker.state is State.CLOSED


def test_semiabierto_se_reabre_si_la_prueba_falla(breaker, reloj):
    for _ in range(3):
        breaker.record_failure()
    reloj.avanzar(10)
    assert breaker.state is State.HALF_OPEN

    breaker.record_failure()

    assert breaker.state is State.OPEN


# --------------------------- Reintentos del cliente ---------------------------

def _settings(**overrides) -> Settings:
    base = dict(retry_attempts=3, retry_backoff_seconds=0.0, auth_timeout_seconds=1.0,
                breaker_failure_threshold=2, breaker_recovery_seconds=10)
    base.update(overrides)
    return Settings(**base)


def _client(handler, settings: Settings | None = None, breaker: CircuitBreaker | None = None):
    settings = settings or _settings()
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler),
                             base_url="http://auth-service")
    return AuthClient(http, settings, breaker), http


async def test_reintenta_ante_falla_de_conexion_y_termina_bien():
    intentos = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        intentos["n"] += 1
        if intentos["n"] < 3:
            raise httpx.ConnectError("conexión rechazada", request=request)
        return httpx.Response(200, json={
            "access_token": "t", "expires_at": "2030-01-01T00:00:00Z",
            "user": {"id": "1", "username": "ana", "email": "ana@example.com"}})

    client, http = _client(handler)
    try:
        user, token = await client.login("ana", "Segura123")
    finally:
        await http.aclose()

    assert intentos["n"] == 3      # dos fallas transitorias + éxito
    assert token == "t"
    assert user.username == "ana"


async def test_reintenta_ante_5xx():
    intentos = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        intentos["n"] += 1
        if intentos["n"] == 1:
            return httpx.Response(503, json={"code": "x", "message": "caído"})
        return httpx.Response(201, json={"id": "1", "username": "ana",
                                         "email": "ana@example.com"})

    client, http = _client(handler)
    try:
        await client.register("ana", "ana@example.com", "Segura123")
    finally:
        await http.aclose()

    assert intentos["n"] == 2


async def test_no_reintenta_ante_4xx():
    """Un 401 es una decisión de negocio: reintentarlo sería inútil y dañino."""
    intentos = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        intentos["n"] += 1
        return httpx.Response(401, json={"code": "invalid_credentials",
                                         "message": "Usuario o contraseña incorrectos",
                                         "request_id": "r1"})

    client, http = _client(handler)
    try:
        with pytest.raises(AuthApiError) as error:
            await client.login("ana", "mala")
    finally:
        await http.aclose()

    assert intentos["n"] == 1
    assert error.value.code == "invalid_credentials"


async def test_agotar_los_reintentos_produce_servicio_no_disponible():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timeout", request=request)

    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=10)
    client, http = _client(handler, breaker=breaker)
    try:
        with pytest.raises(AuthServiceUnavailable):
            await client.login("ana", "Segura123")
    finally:
        await http.aclose()

    # La falla abre el circuito: la siguiente llamada ni siquiera sale.
    assert breaker.state is State.OPEN


async def test_con_el_circuito_abierto_no_se_llama_al_microservicio():
    llamadas = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        llamadas["n"] += 1
        return httpx.Response(200, json={})

    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=10)
    breaker.record_failure()
    client, http = _client(handler, breaker=breaker)
    try:
        with pytest.raises(AuthServiceUnavailable):
            await client.login("ana", "Segura123")
    finally:
        await http.aclose()

    assert llamadas["n"] == 0


async def test_el_request_id_viaja_hacia_el_tier_2():
    from app.core.logging import request_id_var

    capturado = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["request_id"] = request.headers.get("X-Request-ID")
        capturado["actor"] = request.headers.get("X-Actor")
        return httpx.Response(200, json={"user_id": "1", "username": "ana",
                                         "email": "ana@example.com", "valid": True})

    request_id_var.set("traza-web-123")
    client, http = _client(handler)
    try:
        await client.verify("token")
    finally:
        await http.aclose()

    assert capturado["request_id"] == "traza-web-123"
