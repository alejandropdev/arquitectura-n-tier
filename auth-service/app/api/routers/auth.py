"""Capa de exposición: endpoints de autenticación.

Los controladores no contienen lógica de negocio: validan el contrato, delegan en
el caso de uso y traducen el resultado. Los errores los maneja `error_handlers`.
"""

from __future__ import annotations

from typing import Annotated

from auth_common.claims import TokenClaims as AuthCommonClaims
from fastapi import APIRouter, Depends, Request, Response, status

from app.api.dependencies import get_authenticate_user, get_register_user, get_verify_token, require_auth_dep
from app.api.schemas import (
    ErrorResponse,
    IntrospectResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    SessionUserResponse,
    UserResponse,
    VerifyRequest,
    VerifyResponse,
)
from app.application.authenticate_user import AuthenticateUser, AuthenticateUserCommand
from app.application.register_user import RegisterUser, RegisterUserCommand
from app.application.verify_token import VerifyToken
from app.core.logging import actor_var, client_ip_var

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_ERRORS = {
    401: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    423: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


@router.post("/register", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED, responses=_ERRORS)
def register(
    payload: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user)],
) -> UserResponse:
    actor_var.set(payload.username)
    user = use_case.execute(
        RegisterUserCommand(
            username=payload.username, email=str(payload.email), password=payload.password
        )
    )
    return UserResponse(id=user.id, username=user.username, email=user.email,
                        role=user.role, created_at=user.created_at)


@router.post("/login", response_model=LoginResponse, responses=_ERRORS)
def login(
    payload: LoginRequest,
    request: Request,
    use_case: Annotated[AuthenticateUser, Depends(get_authenticate_user)],
) -> LoginResponse:
    actor_var.set(payload.username)
    session = use_case.execute(
        AuthenticateUserCommand(
            username=payload.username,
            password=payload.password,
            client_ip=client_ip_var.get(),
        )
    )
    return LoginResponse(
        access_token=session.access_token,
        expires_at=session.expires_at,
        user=SessionUserResponse(
            id=session.user_id, username=session.username, email=session.email
        ),
    )


@router.post("/verify", response_model=VerifyResponse, responses=_ERRORS)
def verify(
    payload: VerifyRequest,
    use_case: Annotated[VerifyToken, Depends(get_verify_token)],
) -> VerifyResponse:
    identity = use_case.execute(payload.token)
    actor_var.set(identity.username)
    return VerifyResponse(
        valid=True, user_id=identity.user_id, username=identity.username, email=identity.email
    )


@router.get("/introspect", response_model=IntrospectResponse, responses={401: {"model": ErrorResponse}})
def introspect(
    response: Response,
    claims: Annotated[AuthCommonClaims, Depends(require_auth_dep)],
) -> IntrospectResponse:
    """Validación barata (sin ir a la base de datos) para el `auth_request`
    del gateway (Taller 2, Requerimiento 9a): solo firma/`iss`/`exp`/`aud`.

    Expone `X-User-Id`/`X-User-Role` como encabezados de respuesta para que
    nginx los capture con `auth_request_set` (p. ej. para las reglas de
    rate limiting por token del Requerimiento 10).
    """
    actor_var.set(claims.username)
    response.headers["X-User-Id"] = claims.sub
    response.headers["X-User-Role"] = claims.role
    return IntrospectResponse(sub=claims.sub, role=claims.role)
