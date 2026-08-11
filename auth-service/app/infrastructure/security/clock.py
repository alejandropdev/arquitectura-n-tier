"""Reloj del sistema (implementa el puerto `Clock`).

Se inyecta como dependencia para poder congelar el tiempo en las pruebas de
bloqueo de cuentas sin usar `sleep`.
"""

from __future__ import annotations

from datetime import datetime, timezone


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
