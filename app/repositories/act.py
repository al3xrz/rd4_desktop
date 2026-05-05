from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Act
from app.repositories.base import BaseRepository


class ActRepository(BaseRepository[Act]):
    model = Act

    def get_by_number(self, number: str, include_deleted: bool = False) -> Act | None:
        stmt = select(Act).where(Act.number == number)
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_with_services(self, act_id: int, include_deleted: bool = False) -> Act | None:
        stmt = select(Act).options(selectinload(Act.services)).where(Act.id == act_id)
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_for_contract(self, contract_id: int, include_deleted: bool = False) -> list[Act]:
        return self.list(contract_id=contract_id, include_deleted=include_deleted, limit=None)
