"""Caso de uso: obtener el perfil de un usuario.

Existe para demostrar el Requerimiento 9(c) (autorización por propiedad):
la restricción de "solo su propio recurso, salvo un admin" la aplica la
dependencia `require_owner_or_admin` en la capa `api` — este caso de uso no
sabe nada de tokens ni de quién hace la petición, solo resuelve el dato.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.application.ports import UnitOfWork
from app.domain.exceptions import UserNotFound


@dataclass(frozen=True)
class UserProfile:
    id: UUID
    username: str
    email: str
    role: str
    created_at: datetime


class GetUserProfile:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, user_id: UUID) -> UserProfile:
        with self._uow as uow:
            user = uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFound()
            return UserProfile(
                id=user.id, username=user.username, email=user.email,
                role=user.role, created_at=user.created_at,
            )
