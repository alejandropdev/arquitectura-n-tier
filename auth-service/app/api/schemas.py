"""Contratos de entrada/salida de la API (capa de exposición).

La validación estricta con Pydantic es una táctica de *prevención de fallas*:
las peticiones malformadas se rechazan antes de tocar el negocio o la base de datos.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    created_at: datetime


class SessionUserResponse(BaseModel):
    id: UUID
    username: str
    email: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: SessionUserResponse


class VerifyResponse(BaseModel):
    valid: bool
    user_id: UUID
    username: str
    email: str


class ErrorResponse(BaseModel):
    """Contrato uniforme de error; el Tier 1 lo interpreta para mostrar la vista."""

    code: str
    message: str
    request_id: str
    detail: dict | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    instance: str
    dependencies: dict[str, str] = {}
