from __future__ import annotations

from app.models import ActMedService
from app.repositories.base import BaseRepository


class ActMedServiceRepository(BaseRepository[ActMedService]):
    model = ActMedService

    def list_for_act(self, act_id: int, include_deleted: bool = False) -> list[ActMedService]:
        return self.list(act_id=act_id, include_deleted=include_deleted, limit=None)
