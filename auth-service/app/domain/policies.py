"""Políticas del dominio: reglas de negocio puras y verificables por unidad."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.exceptions import InvalidUsername, WeakPassword

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9._-]{3,32}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True)
class PasswordPolicy:
    """Táctica de *prevención de fallas*: rechazar credenciales débiles en el origen."""

    min_length: int = 8
    max_length: int = 128
    require_upper: bool = True
    require_lower: bool = True
    require_digit: bool = True

    def validate(self, password: str) -> None:
        reasons: list[str] = []
        if len(password) < self.min_length:
            reasons.append(f"Debe tener al menos {self.min_length} caracteres")
        if len(password) > self.max_length:
            reasons.append(f"No puede superar {self.max_length} caracteres")
        if self.require_upper and not any(c.isupper() for c in password):
            reasons.append("Debe incluir al menos una letra mayúscula")
        if self.require_lower and not any(c.islower() for c in password):
            reasons.append("Debe incluir al menos una letra minúscula")
        if self.require_digit and not any(c.isdigit() for c in password):
            reasons.append("Debe incluir al menos un dígito")
        if reasons:
            raise WeakPassword(reasons)


@dataclass(frozen=True)
class IdentityPolicy:
    """Formato válido de nombre de usuario y correo."""

    def validate_username(self, username: str) -> None:
        if not _USERNAME_RE.match(username or ""):
            raise InvalidUsername(
                "El usuario debe tener entre 3 y 32 caracteres alfanuméricos, '.', '_' o '-'"
            )

    def validate_email(self, email: str) -> None:
        if not _EMAIL_RE.match(email or ""):
            raise InvalidUsername("El correo electrónico no tiene un formato válido")


@dataclass(frozen=True)
class LockoutPolicy:
    """Bloqueo temporal tras N intentos fallidos (mitiga fuerza bruta)."""

    max_attempts: int = 5
    lockout_seconds: int = 300
