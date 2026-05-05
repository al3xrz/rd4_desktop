from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session


ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Shared CRUD helper for SQLAlchemy ORM models.

    Repositories are intentionally thin: they translate common persistence
    operations into SQLAlchemy calls, but they do not own business rules and never
    commit transactions. Service objects decide where a business operation starts
    and ends; repositories may only flush so callers can receive generated IDs.
    """

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        """Bind the repository to the service-level SQLAlchemy session."""
        self.session = session

    def create(self, **data: Any) -> ModelT:
        """Create and flush a model instance without committing the transaction."""
        item = self.model(**data)
        self.session.add(item)
        self.session.flush()
        return item

    def get(self, item_id: int, include_deleted: bool = False) -> ModelT | None:
        """Return one row by primary key, hiding soft-deleted rows by default."""
        stmt = select(self.model).where(self.model.id == item_id)
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()

    def list(
        self,
        *,
        skip: int = 0,
        limit: int | None = 100,
        include_deleted: bool = False,
        **filters: Any,
    ) -> list[ModelT]:
        """Return rows matching simple equality filters.

        The method is intentionally generic and conservative. More complex
        queries belong in a concrete repository where joins, ordering, eager
        loading, and indexes can be chosen explicitly.
        """
        stmt = select(self.model).filter_by(**filters).offset(skip)
        stmt = self._exclude_deleted(stmt, include_deleted)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def update(self, item_id: int, data: dict[str, Any], include_deleted: bool = False) -> ModelT | None:
        """Patch known model attributes and flush them to the current session."""
        item = self.get(item_id, include_deleted=include_deleted)
        if item is None:
            return None

        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        self.session.flush()
        return item

    def soft_delete(self, item_id: int) -> bool:
        """Mark a row as deleted when the model supports soft deletion.

        A few technical models may not have a ``deleted`` column; those still fall
        back to a physical delete. Business entities in this app should keep their
        soft-delete column so historical data is preserved.
        """
        item = self.get(item_id)
        if item is None:
            return False

        if hasattr(item, "deleted"):
            setattr(item, "deleted", True)
            self.session.flush()
            return True

        self.session.delete(item)
        self.session.flush()
        return True

    def _exclude_deleted(self, stmt, include_deleted: bool):
        """Apply the common ``deleted = false`` predicate when available."""
        if not include_deleted and hasattr(self.model, "deleted"):
            stmt = stmt.where(self.model.deleted.is_(False))
        return stmt
