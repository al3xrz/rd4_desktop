from __future__ import annotations

from app.models import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    def list_for_contract(self, contract_id: int, include_deleted: bool = False) -> list[Payment]:
        return self.list(contract_id=contract_id, include_deleted=include_deleted, limit=None)
