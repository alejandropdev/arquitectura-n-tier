"""Composición de dependencias (inyección manual).

Aquí es donde la infraestructura se enchufa a los puertos de la aplicación. Es el
único punto del microservicio donde se conocen ambas cosas a la vez.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.application.authenticate_user import AuthenticateUser
from app.application.register_user import RegisterUser
from app.application.verify_token import VerifyToken
from app.core.config import Settings, get_settings
from app.domain.policies import IdentityPolicy, LockoutPolicy, PasswordPolicy
from app.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.clock import SystemClock
from app.infrastructure.security.hasher import Argon2PasswordHasher
from app.infrastructure.security.jwt_provider import JwtTokenProvider

SettingsDep = Annotated[Settings, Depends(get_settings)]


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
