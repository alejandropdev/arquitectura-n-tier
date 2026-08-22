"""Capa de exposición: perfil de usuario.

Existe para demostrar el Requerimiento 9(c): un usuario solo puede leer su
propio recurso; un admin puede leer cualquiera. La regla la aplica
`require_owner_or_admin` (`app/api/dependencies.py`), construida sobre la
librería compartida `auth_common`.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from auth_common.claims import TokenClaims as AuthCommonClaims
from fastapi import APIRouter, Depends

from app.api.dependencies import get_get_user_profile, require_owner_or_admin
from app.api.schemas import ErrorResponse, UserProfileResponse
from app.application.get_user_profile import GetUserProfile
from app.core.logging import actor_var

router = APIRouter(prefix="/api/v1/users", tags=["users"])

_ERRORS = {
    401: {"model": ErrorResponse},
    403: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
}


@router.get("/{id}", response_model=UserProfileResponse, responses=_ERRORS)
def get_user(
    id: UUID,
    use_case: Annotated[GetUserProfile, Depends(get_get_user_profile)],
    claims: Annotated[AuthCommonClaims, Depends(require_owner_or_admin)],
) -> UserProfileResponse:
    actor_var.set(claims.username)
    profile = use_case.execute(id)
    return UserProfileResponse(
        id=profile.id, username=profile.username, email=profile.email,
        role=profile.role, created_at=profile.created_at,
    )
