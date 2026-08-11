"""Excepciones del Tier 1 (presentación)."""

from __future__ import annotations


class PresentationError(Exception):
    code = "presentation_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthServiceUnavailable(PresentationError):
    """El Tier 2 no respondió (timeout, conexión, 5xx) o el circuito está abierto."""

    code = "auth_service_unavailable"

    def __init__(self, message: str = "El servicio de autenticación no está disponible. "
                                      "Intente de nuevo en unos segundos.") -> None:
        super().__init__(message)


class AuthApiError(PresentationError):
    """Respuesta 4xx del Tier 2: es un error de negocio, no una falla del sistema."""

    code = "auth_api_error"

    def __init__(self, code: str, message: str, status_code: int,
                 detail: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}

    @property
    def reasons(self) -> list[str]:
        raw = self.detail.get("reasons") or self.detail.get("fields") or []
        return [str(r) for r in raw]


class SessionExpired(PresentationError):
    code = "session_expired"

    def __init__(self) -> None:
        super().__init__("Su sesión expiró. Vuelva a iniciar sesión.")
