from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Contract
from app.repositories.base import BaseRepository


class ContractRepository(BaseRepository[Contract]):
    model = Contract

    def get_by_number(self, contract_number: str, include_deleted: bool = False) -> Contract | None:
        stmt = select(Contract).where(Contract.contract_number == contract_number)
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_with_details(self, contract_id: int, include_deleted: bool = False) -> Contract | None:
        stmt = (
            select(Contract)
            .options(selectinload(Contract.payments), selectinload(Contract.acts))
            .where(Contract.id == contract_id)
        )
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()
