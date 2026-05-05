from __future__ import annotations

from app.core.database import session_scope
from app.core.security import hash_password
from app.models import Role, User
from app.repositories import UserRepository


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"


def ensure_initial_admin() -> bool:
    with session_scope() as session:
        users = UserRepository(session)
        if users.list(limit=1):
            return False

        users.create(
            username=DEFAULT_ADMIN_USERNAME,
            name="Administrator",
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=Role.ADMIN,
            is_active=True,
            comments="Initial desktop administrator",
        )
        return True
