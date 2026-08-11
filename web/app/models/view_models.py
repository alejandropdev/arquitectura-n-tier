"""Modelos del patrón MVC (Tier 1).

Son *view models*: representan lo que la vista necesita mostrar y lo que el
formulario envía. El Tier 1 no tiene modelo de datos propio — los datos viven en
el Tier 3 y solo se acceden a través del Tier 2.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class SessionUser(BaseModel):
    id: str
    username: str
    email: str
    expires_at: str | None = None


class LoginForm(BaseModel):
    """Validación en el borde: evita viajes inútiles al Tier 2."""

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class RegisterForm(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3, max_length=32)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    password_confirm: str = Field(min_length=8, max_length=128)

    def check_confirmation(self) -> list[str]:
        return [] if self.password == self.password_confirm else [
            "Las contraseñas no coinciden"
        ]


def form_errors(error: ValidationError) -> list[str]:
    """Traduce los errores de Pydantic a mensajes legibles en español."""
    messages: list[str] = []
    for item in error.errors():
        field = str(item["loc"][-1]) if item["loc"] else "campo"
        messages.append(f"{field}: {item['msg']}")
    return messages
