from __future__ import annotations

from app.core.database import session_scope
from app.core.security import hash_password, verify_password
from app.models import Role, User
from app.repositories import UserRepository
from app.services.exceptions import DuplicateError, NotFoundError, PermissionDeniedError, ValidationError


class AuthService:
    """Application service responsible for login and user administration.

    Every public method opens exactly one service-level transaction. Repository
    methods inside those transactions only read, write, and flush; this keeps the
    transaction boundary easy to reason about from UI code.
    """

    def login(self, username: str, password: str) -> User:
        """Authenticate an active user and return the ORM user object."""
        with session_scope() as session:
            user = UserRepository(session).get_by_username(username)
            if user is None or not user.is_active or not verify_password(password, user.hashed_password):
                raise PermissionDeniedError("Invalid username or password.")
            return user

    def list_login_users(self) -> list[User]:
        """Return active users shown on the login form."""
        with session_scope() as session:
            return UserRepository(session).list_active()

    def create_user(self, data: dict, current_user: User | None = None) -> User:
        """Create a user account, hashing the plain password before persistence."""
        self._require_admin(current_user)

        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            raise ValidationError("Username and password are required.")

        with session_scope() as session:
            users = UserRepository(session)
            if users.get_by_username(username):
                raise DuplicateError(f"User already exists: {username}")

            role = data.get("role", Role.OPERATOR)
            if isinstance(role, str):
                role = Role(role)

            return users.create(
                username=username,
                name=data.get("name"),
                hashed_password=hash_password(password),
                role=role,
                comments=data.get("comments"),
                is_active=data.get("is_active", True),
            )

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """Let a user change their password after validating the old password."""
        with session_scope() as session:
            users = UserRepository(session)
            user = users.get(user_id)
            if user is None:
                raise NotFoundError(f"User not found: {user_id}")
            if not verify_password(old_password, user.hashed_password):
                raise PermissionDeniedError("Invalid old password.")
            users.update(user_id, {"hashed_password": hash_password(new_password)})

    def reset_password(self, user_id: int, new_password: str, current_user: User | None) -> None:
        """Replace a user's password without knowing the previous password."""
        self._require_admin(current_user)

        with session_scope() as session:
            users = UserRepository(session)
            user = users.get(user_id)
            if user is None:
                raise NotFoundError(f"User not found: {user_id}")
            users.update(user_id, {"hashed_password": hash_password(new_password)})

    def list_users(self, current_user: User | None) -> list[User]:
        """Return all user accounts for the administration screen."""
        self._require_admin(current_user)

        with session_scope() as session:
            return UserRepository(session).list(limit=None)

    def update_user(self, user_id: int, data: dict, current_user: User | None) -> User:
        """Update user profile, role, status, or comments.

        Password fields are explicitly ignored here so password changes remain in
        dedicated flows with clearer authorization and validation.
        """
        self._require_admin(current_user)

        payload = dict(data)
        if "role" in payload and isinstance(payload["role"], str):
            payload["role"] = Role(payload["role"])
        payload.pop("password", None)
        payload.pop("hashed_password", None)

        with session_scope() as session:
            users = UserRepository(session)
            user = users.update(user_id, payload)
            if user is None:
                raise NotFoundError(f"User not found: {user_id}")
            return user

    def set_user_active(self, user_id: int, is_active: bool, current_user: User | None) -> User:
        """Block or unblock a user account."""
        self._require_admin(current_user)

        with session_scope() as session:
            users = UserRepository(session)
            user = users.update(user_id, {"is_active": is_active})
            if user is None:
                raise NotFoundError(f"User not found: {user_id}")
            return user

    def _require_admin(self, current_user: User | None) -> None:
        """Raise when an administrative operation is attempted by a non-admin."""
        if current_user is not None and current_user.role != Role.ADMIN:
            raise PermissionDeniedError("Admin role is required.")
