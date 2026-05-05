from __future__ import annotations

from app.core.database import session_scope
from app.models import MedService
from app.repositories import MedServiceRepository
from app.services.exceptions import BusinessRuleError, NotFoundError


class MedServiceService:
    def create_folder(self, data: dict) -> MedService:
        payload = dict(data)
        payload["is_folder"] = True
        payload["unit"] = ""
        payload["price"] = 0
        payload["vat"] = 0
        return self._create(payload)

    def create_service(self, data: dict) -> MedService:
        payload = dict(data)
        payload["is_folder"] = False
        return self._create(payload)

    def update_med_service(self, service_id: int, data: dict) -> MedService:
        with session_scope() as session:
            repo = MedServiceRepository(session)
            service = repo.get(service_id)
            if service is None:
                raise NotFoundError(f"Med service not found: {service_id}")

            parent_id = data.get("parent_id", service.parent_id)
            self._validate_parent(repo, service_id, parent_id)

            if service.is_folder:
                data = dict(data)
                data["unit"] = ""
                data["price"] = 0
                data["vat"] = 0

            updated = repo.update(service_id, data)
            if updated is None:
                raise NotFoundError(f"Med service not found: {service_id}")
            return updated

    def delete_med_service(self, service_id: int) -> None:
        with session_scope() as session:
            if not MedServiceRepository(session).soft_delete(service_id):
                raise NotFoundError(f"Med service not found: {service_id}")

    def get_med_service(self, service_id: int) -> MedService:
        with session_scope() as session:
            service = MedServiceRepository(session).get(service_id)
            if service is None:
                raise NotFoundError(f"Med service not found: {service_id}")
            return service

    def get_tree(self) -> list[MedService]:
        with session_scope() as session:
            roots = MedServiceRepository(session).get_tree()
            self._load_children(roots)
            return roots

    def list_services(self) -> list[MedService]:
        with session_scope() as session:
            return MedServiceRepository(session).list(limit=None)

    def list_folders(self) -> list[MedService]:
        return [service for service in self.list_services() if service.is_folder]

    def _create(self, data: dict) -> MedService:
        with session_scope() as session:
            repo = MedServiceRepository(session)
            parent_id = data.get("parent_id")
            self._validate_parent(repo, None, parent_id)
            return repo.create(**data)

    def _validate_parent(self, repo: MedServiceRepository, service_id: int | None, parent_id: int | None) -> None:
        if parent_id is None:
            return
        if service_id is not None and parent_id == service_id:
            raise BusinessRuleError("Med service cannot be parent of itself.")

        parent = repo.get(parent_id)
        if parent is None or not parent.is_folder:
            raise BusinessRuleError("Parent must be an existing folder.")

        current = parent
        while current is not None:
            if service_id is not None and current.parent_id == service_id:
                raise BusinessRuleError("Med service tree cannot contain cycles.")
            current = current.parent

    def _load_children(self, services: list[MedService]) -> None:
        for service in services:
            self._load_children(list(service.children))
