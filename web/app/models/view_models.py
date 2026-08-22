"""Modelos del patrón MVC (Tier 1).

Son *view models*: representan lo que la vista necesita mostrar y lo que el
formulario envía. El Tier 1 no tiene modelo de datos propio — los datos viven en
el Tier 3 y solo se acceden a través del Tier 2.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

PRODUCT_STATUSES: tuple[str, ...] = ("borrador", "activo", "descontinuado")
ProductStatus = Literal["borrador", "activo", "descontinuado"]


class SessionUser(BaseModel):
    id: str
    username: str
    email: str
    role: str = "user"
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


class ProductForm(BaseModel):
    """Validación en el borde para alta/edición de productos.

    Refleja las mismas reglas que `CreateProductDto` en el Tier 2: evita viajes
    inútiles cuando el error es evidente desde el navegador.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    brand: str | None = Field(default=None, max_length=100)
    category_id: str = Field(min_length=1, max_length=64)
    status: ProductStatus = "borrador"


class ProductListQuery(BaseModel):
    """Filtros de listado; también se usa para mantener los valores en la vista."""

    model_config = ConfigDict(str_strip_whitespace=True)

    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    search: str | None = Field(default=None, max_length=150)
    status: ProductStatus | None = None
    brand: str | None = Field(default=None, max_length=100)
    category_id: str | None = Field(default=None, max_length=64)
    sort: Literal["createdAt", "name"] = "createdAt"
    order: Literal["ASC", "DESC"] = "DESC"

    def to_query_params(self) -> dict[str, str | int]:
        params: dict[str, str | int] = {
            "page": self.page, "size": self.size, "sort": self.sort, "order": self.order,
        }
        if self.search:
            params["search"] = self.search
        if self.status:
            params["status"] = self.status
        if self.brand:
            params["brand"] = self.brand
        if self.category_id:
            params["categoryId"] = self.category_id
        return params


def form_errors(error: ValidationError) -> list[str]:
    """Traduce los errores de Pydantic a mensajes legibles en español."""
    messages: list[str] = []
    for item in error.errors():
        field = str(item["loc"][-1]) if item["loc"] else "campo"
        messages.append(f"{field}: {item['msg']}")
    return messages
