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
