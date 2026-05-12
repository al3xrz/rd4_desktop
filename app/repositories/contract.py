from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import noload, selectinload

from app.models import Act, ActMedService, Contract, Payment
from app.repositories.base import BaseRepository


class ContractRepository(BaseRepository[Contract]):
    model = Contract

    def list(
        self,
        *,
        skip: int = 0,
        limit: int | None = 100,
        include_deleted: bool = False,
        **filters,
    ) -> list[Contract]:
        stmt = select(Contract).options(noload(Contract.payments), noload(Contract.acts)).filter_by(**filters).offset(skip)
        stmt = self._exclude_deleted(stmt, include_deleted)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_number(self, contract_number: str, include_deleted: bool = False) -> Contract | None:
        stmt = select(Contract).where(Contract.contract_number == contract_number)
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_with_details(self, contract_id: int, include_deleted: bool = False) -> Contract | None:
        stmt = (
            select(Contract)
            .options(selectinload(Contract.payments), selectinload(Contract.acts).selectinload(Act.services))
            .where(Contract.id == contract_id)
        )
        stmt = self._exclude_deleted(stmt, include_deleted)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_summaries(self, include_deleted: bool = False) -> dict[int, dict]:
        services_total = (
            select(
                Act.contract_id.label("contract_id"),
                func.coalesce(
                    func.sum(
                        ActMedService.price
                        * ActMedService.count
                        * (1 - (ActMedService.discount / 100))
                    ),
                    0,
                ).label("services_total"),
            )
            .join(ActMedService, ActMedService.act_id == Act.id)
            .where(Act.deleted.is_(False), ActMedService.deleted.is_(False))
            .group_by(Act.contract_id)
            .subquery()
        )
        payments_total = (
            select(
                Payment.contract_id.label("contract_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("payments_total"),
            )
            .where(Payment.deleted.is_(False), Payment.posted.is_(True))
            .group_by(Payment.contract_id)
            .subquery()
        )
        refunds_total = (
            select(
                Payment.contract_id.label("contract_id"),
                func.coalesce(func.sum(Payment.amount), 0).label("refunds_total"),
            )
            .where(Payment.deleted.is_(False), Payment.posted.is_(True), Payment.amount < 0)
            .group_by(Payment.contract_id)
            .subquery()
        )

        stmt = (
            select(
                Contract.id,
                func.coalesce(services_total.c.services_total, 0),
                func.coalesce(payments_total.c.payments_total, 0),
                func.coalesce(refunds_total.c.refunds_total, 0),
            )
            .outerjoin(services_total, services_total.c.contract_id == Contract.id)
            .outerjoin(payments_total, payments_total.c.contract_id == Contract.id)
            .outerjoin(refunds_total, refunds_total.c.contract_id == Contract.id)
        )
        stmt = self._exclude_deleted(stmt, include_deleted)

        summaries = {}
        for contract_id, services, payments, refunds in self.session.execute(stmt).all():
            balance = payments - services
            status = "paid"
            if balance < 0:
                status = "debt"
            elif balance > 0:
                status = "overpaid"
            summaries[contract_id] = {
                "services_total": services,
                "payments_total": payments,
                "refunds_total": refunds,
                "balance": balance,
                "status": status,
            }
        return summaries
