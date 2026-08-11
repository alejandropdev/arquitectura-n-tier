"""Excepciones de la capa de dominio.

El dominio no conoce HTTP: expresa fallas del negocio. La capa `api` las traduce
a códigos de estado (ver `app/api/error_handlers.py`).
"""

from __future__ import annotations


class DomainError(Exception):
    """Raíz de todas las fallas de negocio."""

    code = "domain_error"

    def __init__(self, message: str, **context) -> None:
        super().__init__(message)
        self.message = message
        self.context = context


class InvalidCredentials(DomainError):
    code = "invalid_credentials"

    def __init__(self, message: str = "Usuario o contraseña incorrectos") -> None:
        super().__init__(message)


class UserAlreadyExists(DomainError):
    code = "user_already_exists"

    def __init__(self, field: str = "username") -> None:
        super().__init__(f"Ya existe un usuario con ese {field}", field=field)


class UserNotFound(DomainError):
    code = "user_not_found"

    def __init__(self, message: str = "El usuario no existe") -> None:
        super().__init__(message)


class AccountLocked(DomainError):
    code = "account_locked"

    def __init__(self, seconds_left: int) -> None:
        super().__init__(
            f"Cuenta bloqueada temporalmente. Intente de nuevo en {seconds_left} segundos.",
            seconds_left=seconds_left,
        )
        self.seconds_left = seconds_left


class AccountInactive(DomainError):
    code = "account_inactive"

    def __init__(self) -> None:
        super().__init__("La cuenta está desactivada")


class WeakPassword(DomainError):
    code = "weak_password"

    def __init__(self, reasons: list[str]) -> None:
        super().__init__("La contraseña no cumple la política de seguridad", reasons=reasons)
        self.reasons = reasons


class InvalidUsername(DomainError):
    code = "invalid_username"


class InvalidToken(DomainError):
    code = "invalid_token"

    def __init__(self, message: str = "Token inválido o expirado") -> None:
        super().__init__(message)
