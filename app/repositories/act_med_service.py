from __future__ import annotations

from sqlalchemy import select

from app.models import Act, ActMedService
from app.repositories.base import BaseRepository


class ActMedServiceRepository(BaseRepository[ActMedService]):
    model = ActMedService

    def list_for_act(self, act_id: int, include_deleted: bool = False) -> list[ActMedService]:
        return self.list(act_id=act_id, include_deleted=include_deleted, limit=None)

    def list_service_report_rows(self, date_from, date_to) -> list[ActMedService]:
        stmt = (
            select(ActMedService)
            .join(Act, Act.id == ActMedService.act_id)
            .where(
                Act.deleted.is_(False),
                ActMedService.deleted.is_(False),
                Act.date >= date_from,
                Act.date < date_to,
            )
            .order_by(Act.date, ActMedService.current_name, ActMedService.price)
        )
        return list(self.session.execute(stmt).scalars().all())
