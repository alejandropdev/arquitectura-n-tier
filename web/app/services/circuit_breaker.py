"""Circuit breaker — táctica de **prevención de fallas**.

Si el Tier 2 está caído, seguir enviándole peticiones solo consume hilos, agota
timeouts y degrada al Tier 1. El interruptor corta el tráfico y responde de
inmediato mientras la dependencia se recupera.

    CERRADO  --(N fallas consecutivas)-->  ABIERTO
    ABIERTO  --(pasan T segundos)------->  SEMIABIERTO
    SEMIABIERTO --(éxito)--------------->  CERRADO
    SEMIABIERTO --(falla)--------------->  ABIERTO
"""

from __future__ import annotations

import time
from enum import Enum

from app.core.logging import audit, get_logger

_logger = get_logger("services")


class State(str, Enum):
    CLOSED = "cerrado"
    OPEN = "abierto"
    HALF_OPEN = "semiabierto"


class CircuitOpenError(Exception):
    """El circuito está abierto: no se intenta la llamada."""


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 15.0,
                 name: str = "auth-service", time_source=time.monotonic) -> None:
        self._threshold = failure_threshold
        self._recovery = recovery_seconds
        self._name = name
        self._now = time_source
        self._failures = 0
        self._opened_at: float | None = None
        self._state = State.CLOSED

    @property
    def state(self) -> State:
        if self._state is State.OPEN and self._opened_at is not None:
            if self._now() - self._opened_at >= self._recovery:
                self._transition(State.HALF_OPEN, "Ventana de recuperación cumplida")
        return self._state

    def before_call(self) -> None:
        if self.state is State.OPEN:
            audit(_logger, "breaker.reject", "FAILURE", component="CircuitBreaker",
                  actor="system", message=f"Circuito abierto hacia {self._name}")
            raise CircuitOpenError(f"Circuito abierto hacia {self._name}")

    def record_success(self) -> None:
        if self._state is not State.CLOSED:
            self._transition(State.CLOSED, "Llamada exitosa en estado semiabierto")
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        if self._state is State.HALF_OPEN:
            self._failures = self._threshold
            self._opened_at = self._now()
            self._transition(State.OPEN, "Falla durante la prueba de recuperación")
            return

        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._now()
            self._transition(State.OPEN, f"{self._failures} fallas consecutivas")

    def _transition(self, new_state: State, reason: str) -> None:
        previous, self._state = self._state, new_state
        audit(_logger, "breaker.transition", "INFO", component="CircuitBreaker", actor="system",
              message=f"Circuito {previous.value} -> {new_state.value}: {reason}",
              dependency=self._name, previous_state=previous.value, new_state=new_state.value)
