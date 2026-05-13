from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import session_scope
from app.models import Act, ActMedService, User
from app.repositories import ActMedServiceRepository, ActRepository, ContractRepository, MedServiceRepository
from app.services.exceptions import BusinessRuleError, DuplicateError, NotFoundError


class ActService:
    def create_act(self, contract_id: int, data: dict, current_user: User) -> Act:
        services_data = data.pop("services", [])

        with session_scope() as session:
            current_user = session.merge(current_user)
            contracts = ContractRepository(session)
            contract = contracts.get(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")

            acts = ActRepository(session)
            if acts.get_by_number(data["number"]):
                raise DuplicateError(f"Act already exists: {data['number']}")

            payload = dict(data)
            payload.setdefault("date", datetime.now(timezone.utc))
            act = acts.create(contract=contract, user=current_user, **payload)

            rows = ActMedServiceRepository(session)
            med_services = MedServiceRepository(session)
            for service_data in services_data:
                self._add_or_increment_service_row(rows, med_services, act, service_data)

            return act

    def update_act(self, act_id: int, data: dict, current_user: User | None = None) -> Act:
        data.pop("services", None)
        with session_scope() as session:
            acts = ActRepository(session)
            act = acts.get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            if "number" in data and data["number"] != act.number and acts.get_by_number(data["number"]):
                raise DuplicateError(f"Act already exists: {data['number']}")
            updated = acts.update(act_id, data)
            if updated is None:
                raise NotFoundError(f"Act not found: {act_id}")
            return updated

    def delete_act(self, act_id: int, current_user: User | None = None) -> None:
        with session_scope() as session:
            acts = ActRepository(session)
            rows = ActMedServiceRepository(session)
            act = acts.get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            for row in rows.list_for_act(act_id):
                row.deleted = True
            acts.soft_delete(act_id)

    def add_service(self, act_id: int, med_service_id: int, data: dict, current_user: User | None = None) -> ActMedService:
        with session_scope() as session:
            act = ActRepository(session).get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            med_services = MedServiceRepository(session)
            rows = ActMedServiceRepository(session)
            return self._add_or_increment_service_row(rows, med_services, act, {"med_service_id": med_service_id, **data})

    def update_service_row(self, row_id: int, data: dict, current_user: User | None = None) -> ActMedService:
        immutable = {"current_code", "current_name", "unit", "med_service_id"}
        data = {key: value for key, value in data.items() if key not in immutable}

        with session_scope() as session:
            rows = ActMedServiceRepository(session)
            row = rows.update(row_id, data)
            if row is None:
                raise NotFoundError(f"Act service row not found: {row_id}")
            return row

    def remove_service_row(self, row_id: int, current_user: User | None = None) -> None:
        with session_scope() as session:
            if not ActMedServiceRepository(session).soft_delete(row_id):
                raise NotFoundError(f"Act service row not found: {row_id}")

    def list_acts(self, contract_id: int) -> list[Act]:
        with session_scope() as session:
            return ActRepository(session).list_for_contract(contract_id)

    def get_act(self, act_id: int) -> Act:
        with session_scope() as session:
            act = ActRepository(session).get_with_services(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            return act

    def list_service_rows(self, act_id: int) -> list[ActMedService]:
        with session_scope() as session:
            act = ActRepository(session).get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            return ActMedServiceRepository(session).list_for_act(act_id)

    def _build_service_row(self, med_services: MedServiceRepository, act: Act, data: dict) -> dict:
        med_service = med_services.get(data["med_service_id"])
        if med_service is None or med_service.is_folder:
            raise BusinessRuleError("Only non-folder med service can be added to act.")

        return {
            "act": act,
            "med_service": med_service,
            "current_code": med_service.code,
            "current_name": med_service.name,
            "unit": med_service.unit,
            "price": data.get("price", med_service.price),
            "discount": data.get("discount", 0),
            "count": data.get("count", 1),
            "comments": data.get("comments"),
        }

    def _add_or_increment_service_row(
        self,
        rows: ActMedServiceRepository,
        med_services: MedServiceRepository,
        act: Act,
        data: dict,
    ) -> ActMedService:
        payload = self._build_service_row(med_services, act, data)
        matching_row = self._find_matching_service_row(
            rows.list_for_act(act.id),
            data["med_service_id"],
            payload["discount"],
        )
        if matching_row is None:
            return rows.create(**payload)

        matching_row.count = int(matching_row.count or 0) + int(payload["count"] or 0)
        rows.session.flush()
        return matching_row

    def _find_matching_service_row(
        self,
        rows: list[ActMedService],
        med_service_id: int,
        discount,
    ) -> ActMedService | None:
        expected_discount = Decimal(str(discount or 0))
        for row in rows:
            if row.med_service_id == med_service_id and Decimal(str(row.discount or 0)) == expected_discount:
                return row
        return None
