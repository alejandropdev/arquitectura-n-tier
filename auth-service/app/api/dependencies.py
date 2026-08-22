"""Composición de dependencias (inyección manual).

Aquí es donde la infraestructura se enchufa a los puertos de la aplicación. Es el
único punto del microservicio donde se conocen ambas cosas a la vez.
"""

from __future__ import annotations

from typing import Annotated

from auth_common.fastapi_ext.dependencies import require_auth, require_owner_or_role
from auth_common.settings import AuthCommonSettings
from fastapi import Depends, Request

from app.application.authenticate_user import AuthenticateUser
from app.application.get_user_profile import GetUserProfile
from app.application.register_user import RegisterUser
from app.application.verify_token import VerifyToken
from app.core.config import Settings, get_settings
from app.core.logging import request_id_var
from app.domain.policies import IdentityPolicy, LockoutPolicy, PasswordPolicy
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.clock import SystemClock
from app.infrastructure.security.hasher import Argon2PasswordHasher
from app.infrastructure.security.jwt_provider import JwtTokenProvider

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_auth_common_settings(settings: SettingsDep) -> AuthCommonSettings:
    return AuthCommonSettings(
        jwt_secret=settings.jwt_secret,
        jwt_algorithm=settings.jwt_algorithm,
        jwt_issuer=settings.jwt_issuer,
    )


# Requerimiento 9(a)/(b): auth-service es un resource server — exige que el
# token traiga su propio nombre en `aud`, así un token emitido para otro
# servicio (p. ej. `products-service`) no sirve aquí.
require_auth_dep = require_auth(
    "auth-service",
    get_settings=lambda: get_auth_common_settings(get_settings()),
    get_request_id=lambda: request_id_var.get(),
)

# Requerimiento 9(c): un usuario solo puede leer su propio recurso; un admin
# puede leer cualquiera.
require_owner_or_admin = require_owner_or_role(
    "id", "admin",
    require_auth_dep=require_auth_dep,
    get_request_id=lambda: request_id_var.get(),
)


def get_unit_of_work(request: Request) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(request.app.state.session_factory)


def get_hasher(request: Request) -> Argon2PasswordHasher:
    return request.app.state.hasher


def get_token_provider(settings: SettingsDep) -> JwtTokenProvider:
    return JwtTokenProvider(
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expiration_minutes=settings.jwt_expiration_minutes,
        issuer=settings.jwt_issuer,
        audiences=settings.jwt_audiences,
    )


def get_register_user(
    settings: SettingsDep,
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
    hasher: Annotated[Argon2PasswordHasher, Depends(get_hasher)],
) -> RegisterUser:
    return RegisterUser(
        uow=uow,
        hasher=hasher,
        clock=SystemClock(),
        password_policy=PasswordPolicy(
            min_length=settings.password_min_length,
            max_length=settings.password_max_length,
        ),
        identity_policy=IdentityPolicy(),
    )


def get_authenticate_user(
    settings: SettingsDep,
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
    hasher: Annotated[Argon2PasswordHasher, Depends(get_hasher)],
    tokens: Annotated[JwtTokenProvider, Depends(get_token_provider)],
) -> AuthenticateUser:
    return AuthenticateUser(
        uow=uow,
        hasher=hasher,
        tokens=tokens,
        clock=SystemClock(),
        lockout=LockoutPolicy(
            max_attempts=settings.max_failed_attempts,
            lockout_seconds=settings.lockout_seconds,
        ),
    )


def get_verify_token(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
    tokens: Annotated[JwtTokenProvider, Depends(get_token_provider)],
) -> VerifyToken:
    return VerifyToken(uow=uow, tokens=tokens)


def get_get_user_profile(
    uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> GetUserProfile:
    return GetUserProfile(uow=uow)
