"""Dependencias compartidas por los controladores."""

from __future__ import annotations

from fastapi import Request

from app.core.config import get_settings
from app.core.exceptions import AuthServiceUnavailable, SessionExpired
from app.models.view_models import SessionUser
from app.services.auth_client import AuthClient
from app.services.products_client import ProductsClient


def get_auth_client(request: Request) -> AuthClient:
    return request.app.state.auth_client


def get_products_client(request: Request) -> ProductsClient:
    return request.app.state.products_client


async def get_current_user(request: Request) -> SessionUser:
    """Resuelve la sesión validando el token contra el Tier 2.

    El Tier 1 no interpreta el JWT por su cuenta: la autoridad sobre la sesión
    es el microservicio.
    """
    token = request.cookies.get(get_settings().session_cookie)
    if not token:
        raise SessionExpired()

    client: AuthClient = request.app.state.auth_client
    try:
        return await client.verify(token)
    except AuthServiceUnavailable:
        raise
    except Exception as exc:  # token inválido/expirado -> se pide login otra vez
        raise SessionExpired() from exc
