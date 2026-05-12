from __future__ import annotations

from sqlalchemy import select

from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Persistence helpers specific to application users."""

    model = User

    def get_by_username(self, username: str) -> User | None:
        """Find a user by login name for authentication and uniqueness checks."""
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_active(self) -> list[User]:
        """Return active users for login selection."""
        stmt = select(User).where(User.is_active.is_(True)).order_by(User.name, User.username)
        return list(self.session.execute(stmt).scalars().all())
