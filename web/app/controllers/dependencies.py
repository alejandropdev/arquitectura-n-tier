"""Dependencias compartidas por los controladores."""

from __future__ import annotations

from auth_common.errors import AuthCommonError
from auth_common.tokens import decode_token
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

    El Tier 1 no interpreta el JWT por su cuenta para decidir si la sesión es
    válida: esa sigue siendo autoridad exclusiva del microservicio (`/verify`
    consulta la base de datos, así que respeta cuentas desactivadas/dadas de
    baja). Solo se decodifica localmente, y solo después de que `/verify` ya
    aprobó la sesión, para leer `role` y poder mostrarlo en la vista sin un
    segundo viaje al Tier 2 — si esa decodificación falla por cualquier
    razón, se ignora: no es la fuente de verdad de seguridad, es una
    comodidad de UI.
    """
    token = request.cookies.get(get_settings().session_cookie)
    if not token:
        raise SessionExpired()

    client: AuthClient = request.app.state.auth_client
    try:
        user = await client.verify(token)
    except AuthServiceUnavailable:
        raise
    except Exception as exc:  # token inválido/expirado -> se pide login otra vez
        raise SessionExpired() from exc

    settings = get_settings()
    try:
        claims = decode_token(
            token, secret=settings.jwt_secret, algorithm=settings.jwt_algorithm,
            issuer=settings.jwt_issuer, expected_audience=None,
        )
        user.role = claims.role
    except AuthCommonError:
        pass

    return user
