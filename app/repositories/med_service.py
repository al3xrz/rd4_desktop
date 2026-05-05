from __future__ import annotations

from sqlalchemy import select

from app.models import MedService
from app.repositories.base import BaseRepository


class MedServiceRepository(BaseRepository[MedService]):
    model = MedService

    def list_children(self, parent_id: int | None, include_deleted: bool = False) -> list[MedService]:
        stmt = select(MedService).where(MedService.parent_id.is_(parent_id))
        stmt = self._exclude_deleted(stmt, include_deleted)
        return list(self.session.execute(stmt).scalars().all())

    def get_tree(self, include_deleted: bool = False) -> list[MedService]:
        return self.list_children(None, include_deleted=include_deleted)
