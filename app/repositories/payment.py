from __future__ import annotations

from sqlalchemy import select

from app.models import Payment
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    def list_for_contract(self, contract_id: int, include_deleted: bool = False) -> list[Payment]:
        return self.list(contract_id=contract_id, include_deleted=include_deleted, limit=None)

    def get_posted_by_contract_and_comment(self, contract_id: int, comment: str) -> Payment | None:
        payments = self.list_posted_by_contract_and_comment(contract_id, comment)
        return payments[0] if payments else None

    def list_posted_by_contract_and_comment(self, contract_id: int, comment: str) -> list[Payment]:
        stmt = select(Payment).where(
            Payment.contract_id == contract_id,
            Payment.comments == comment,
            Payment.deleted.is_(False),
            Payment.posted.is_(True),
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_financial_report_rows(self, date_from, date_to) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(
                Payment.deleted.is_(False),
                Payment.posted.is_(True),
                Payment.date >= date_from,
                Payment.date < date_to,
            )
            .order_by(Payment.date, Payment.id)
        )
        return list(self.session.execute(stmt).scalars().all())
