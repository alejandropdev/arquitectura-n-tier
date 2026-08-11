"""Adaptador de hashing de contraseñas (implementa el puerto `PasswordHasher`).

Se usa Argon2id (ganador del Password Hashing Competition y recomendación OWASP).
Nunca se almacena ni se registra la contraseña en claro.
"""

from __future__ import annotations

from argon2 import PasswordHasher as _Argon2
from argon2.exceptions import Argon2Error, VerifyMismatchError

from app.core.logging import audit, get_logger

_logger = get_logger("infrastructure")


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = _Argon2()

    def hash(self, plain: str) -> str:
        return self._hasher.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return self._hasher.verify(hashed, plain)
        except VerifyMismatchError:
            return False
        except Argon2Error as exc:
            # Hash corrupto o con formato desconocido: se trata como fallo de verificación,
            # pero se deja constancia para operación.
            audit(_logger, "security.verify_password", "FAILURE",
                  component="Argon2PasswordHasher",
                  message="No se pudo verificar el hash almacenado",
                  error_code=type(exc).__name__)
            return False
