"""Fábricas de dependencias `Depends`-compatibles para FastAPI.

Cada servicio construye su propia instancia de `require_auth` con la
audiencia que le corresponde (p. ej. `"auth-service"` o
`"products-service"`) — la regla de audiencia queda en configuración, no
hardcodeada, tal como exige el principio de modificabilidad del taller.
`require_role`/`require_owner_or_role` se construyen encima de esa instancia,
así la verificación de audiencia siempre corre primero.
"""

from typing import Callable

from fastapi import Depends, Request

from ..claims import TokenClaims
from ..errors import AuthCommonError, InvalidTokenError, OwnershipForbiddenError, RoleForbiddenError
from ..settings import AuthCommonSettings
from ..tokens import decode_token
from .error_mapping import to_http_exception

RequireAuthDep = Callable[..., TokenClaims]


def _no_request_id() -> str:
    return "-"


def _extract_bearer(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise InvalidTokenError("Falta el encabezado Authorization: Bearer <token>")
    return token


def require_auth(
    expected_audience: str,
    *,
    get_settings: Callable[[], AuthCommonSettings],
    get_request_id: Callable[[], str] = _no_request_id,
) -> RequireAuthDep:
    """Construye una dependencia que exige un JWT válido para `expected_audience`."""

    def _dependency(request: Request) -> TokenClaims:
        try:
            token = _extract_bearer(request)
            settings = get_settings()
            return decode_token(
                token,
                secret=settings.jwt_secret,
                algorithm=settings.jwt_algorithm,
                issuer=settings.jwt_issuer,
                expected_audience=expected_audience,
            )
        except AuthCommonError as exc:
            raise to_http_exception(exc, get_request_id()) from exc

    return _dependency


def require_role(
    *roles: str,
    require_auth_dep: RequireAuthDep,
    get_request_id: Callable[[], str] = _no_request_id,
) -> RequireAuthDep:
    """Construye una dependencia que además exige `claims.role in roles`."""

    def _dependency(claims: TokenClaims = Depends(require_auth_dep)) -> TokenClaims:
        if claims.role not in roles:
            raise to_http_exception(
                RoleForbiddenError("El rol del token no está autorizado para esta operación"),
                get_request_id(),
            )
        return claims

    return _dependency


def require_owner_or_role(
    id_param: str,
    *roles: str,
    require_auth_dep: RequireAuthDep,
    get_request_id: Callable[[], str] = _no_request_id,
) -> RequireAuthDep:
    """Permite la petición si `claims.sub` coincide con el parámetro de ruta
    `id_param`, o si `claims.role` está en `roles`."""

    def _dependency(
        request: Request,
        claims: TokenClaims = Depends(require_auth_dep),
    ) -> TokenClaims:
        resource_id = request.path_params.get(id_param)
        if claims.sub != str(resource_id) and claims.role not in roles:
            raise to_http_exception(
                OwnershipForbiddenError("No puede acceder a un recurso de otro usuario"),
                get_request_id(),
            )
        return claims

    return _dependency
