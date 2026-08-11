"""Traducción entre el modelo físico (ORM) y las entidades del dominio."""

from __future__ import annotations

from app.domain.entities import User
from app.infrastructure.persistence.orm_models import UserRow


def row_to_user(row: UserRow) -> User:
    return User(
        id=row.id,
        username=row.username,
        email=row.email,
        password_hash=row.password_hash,
        is_active=row.is_active,
        failed_attempts=row.failed_attempts,
        locked_until=row.locked_until,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
    )


def user_to_row(user: User) -> UserRow:
    row = UserRow(
        username=user.username,
        email=user.email,
        password_hash=user.password_hash,
        is_active=user.is_active,
        failed_attempts=user.failed_attempts,
        locked_until=user.locked_until,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )
    if user.id is not None:
        row.id = user.id
    return row
