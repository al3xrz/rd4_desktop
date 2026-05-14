from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import session_scope
from app.models import Act, ActMedService, Payment, User
from app.repositories import (
    ActMedServiceRepository,
    ActRepository,
    ContractRepository,
    MedServiceRepository,
    PaymentRepository,
)
from app.services.exceptions import BusinessRuleError, DuplicateError, NotFoundError, ValidationError


class ActService:
    def create_act(
        self,
        contract_id: int,
        data: dict,
        current_user: User,
        *,
        add_payment: bool = False,
        mark_discharged: bool = False,
    ) -> Act:
        services_data = data.pop("services", [])

        with session_scope() as session:
            current_user = session.merge(current_user)
            contracts = ContractRepository(session)
            contract = contracts.get(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")

            acts = ActRepository(session)
            data = dict(data)
            data["number"] = data.get("number") or self._next_act_number(acts, contract)
            if acts.get_by_number(data["number"]):
                raise DuplicateError(f"Act already exists: {data['number']}")

            payload = dict(data)
            payload.setdefault("date", datetime.now(timezone.utc))
            act = acts.create(contract=contract, user=current_user, **payload)

            rows = ActMedServiceRepository(session)
            med_services = MedServiceRepository(session)
            for service_data in services_data:
                self._add_or_increment_service_row(rows, med_services, act, service_data)

            self._apply_save_options(act, rows, current_user, add_payment, mark_discharged)
            return act

    def update_act(
        self,
        act_id: int,
        data: dict,
        current_user: User | None = None,
        *,
        add_payment: bool = False,
        mark_discharged: bool = False,
    ) -> Act:
        data.pop("services", None)
        with session_scope() as session:
            current_user = session.merge(current_user) if current_user is not None else None
            acts = ActRepository(session)
            act = acts.get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            self._ensure_act_editable(PaymentRepository(session), act)
            if "number" in data and data["number"] != act.number and acts.get_by_number(data["number"]):
                raise DuplicateError(f"Act already exists: {data['number']}")
            updated = acts.update(act_id, data)
            if updated is None:
                raise NotFoundError(f"Act not found: {act_id}")
            self._apply_save_options(
                updated,
                ActMedServiceRepository(session),
                current_user,
                add_payment,
                mark_discharged,
            )
            return updated

    def delete_act(self, act_id: int, current_user: User | None = None) -> None:
        with session_scope() as session:
            acts = ActRepository(session)
            rows = ActMedServiceRepository(session)
            payments = PaymentRepository(session)
            act = acts.get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            for row in rows.list_for_act(act_id):
                row.deleted = True
            delete_comment = self._act_delete_payment_comment(act.number)
            for payment in self._act_payments(payments, act):
                payment.deleted = True
                payment.comments = delete_comment
            acts.soft_delete(act_id)

    def pay_act(self, act_id: int, current_user: User) -> Payment:
        with session_scope() as session:
            current_user = session.merge(current_user)
            acts = ActRepository(session)
            rows = ActMedServiceRepository(session)
            payments = PaymentRepository(session)
            act = acts.get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            if self._has_act_payment(payments, act):
                raise BusinessRuleError("По этому акту уже создан платеж. Акт доступен только для просмотра.")
            return self._create_act_payment(act, rows, payments, current_user)

    def add_service(self, act_id: int, med_service_id: int, data: dict, current_user: User | None = None) -> ActMedService:
        with session_scope() as session:
            act = ActRepository(session).get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            self._ensure_act_editable(PaymentRepository(session), act)
            med_services = MedServiceRepository(session)
            rows = ActMedServiceRepository(session)
            return self._add_or_increment_service_row(rows, med_services, act, {"med_service_id": med_service_id, **data})

    def update_service_row(self, row_id: int, data: dict, current_user: User | None = None) -> ActMedService:
        immutable = {"current_code", "current_name", "unit", "med_service_id"}
        data = {key: value for key, value in data.items() if key not in immutable}

        with session_scope() as session:
            rows = ActMedServiceRepository(session)
            existing_row = rows.get(row_id)
            if existing_row is None:
                raise NotFoundError(f"Act service row not found: {row_id}")
            self._ensure_act_editable(PaymentRepository(session), existing_row.act)
            row = rows.update(row_id, data)
            if row is None:
                raise NotFoundError(f"Act service row not found: {row_id}")
            return row

    def remove_service_row(self, row_id: int, current_user: User | None = None) -> None:
        with session_scope() as session:
            rows = ActMedServiceRepository(session)
            row = rows.get(row_id)
            if row is None:
                raise NotFoundError(f"Act service row not found: {row_id}")
            self._ensure_act_editable(PaymentRepository(session), row.act)
            rows.soft_delete(row_id)

    def list_acts(self, contract_id: int) -> list[Act]:
        with session_scope() as session:
            return ActRepository(session).list_for_contract(contract_id, include_deleted=True)

    def get_act(self, act_id: int) -> Act:
        with session_scope() as session:
            act = ActRepository(session).get_with_services(act_id, include_deleted=True)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            return act

    def list_service_rows(self, act_id: int) -> list[ActMedService]:
        with session_scope() as session:
            act = ActRepository(session).get(act_id, include_deleted=True)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            return ActMedServiceRepository(session).list_for_act(act_id, include_deleted=act.deleted)

    def next_act_number(self, contract_id: int) -> str:
        with session_scope() as session:
            contract = ContractRepository(session).get(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")
            return self._next_act_number(ActRepository(session), contract)

    def is_act_paid(self, act_id: int) -> bool:
        with session_scope() as session:
            act = ActRepository(session).get(act_id)
            if act is None:
                raise NotFoundError(f"Act not found: {act_id}")
            return self._has_act_payment(PaymentRepository(session), act)

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

    def _next_act_number(self, acts: ActRepository, contract) -> str:
        act_index = len(acts.list_for_contract(contract.id, include_deleted=True)) + 1
        return f"{contract.contract_number} / {act_index}"

    def _apply_save_options(
        self,
        act: Act,
        rows: ActMedServiceRepository,
        current_user: User | None,
        add_payment: bool,
        mark_discharged: bool,
    ) -> None:
        if mark_discharged:
            act.contract.discharged = True
            if act.contract.discharge_date is None:
                act.contract.discharge_date = act.date
            if current_user is not None:
                act.contract.updated_by_user = current_user

        if add_payment:
            if current_user is None:
                raise ValidationError("Current user is required to create payment by act.")
            if self._has_act_payment(PaymentRepository(rows.session), act):
                raise BusinessRuleError("По этому акту уже создан платеж. Акт доступен только для просмотра.")
            self._create_act_payment(act, rows, PaymentRepository(rows.session), current_user)

        if mark_discharged:
            rows.session.flush()

    def _ensure_act_editable(self, payments: PaymentRepository, act: Act) -> None:
        if self._has_act_payment(payments, act):
            raise BusinessRuleError("По этому акту уже создан платеж. Акт доступен только для просмотра.")

    def _has_act_payment(self, payments: PaymentRepository, act: Act) -> bool:
        return bool(self._act_payments(payments, act))

    def _act_payments(self, payments: PaymentRepository, act: Act):
        return payments.list_posted_by_contract_and_comment(
            act.contract_id,
            self._payment_comment(act.number),
        )

    def _payment_comment(self, act_number: str) -> str:
        return f"Платеж по акту {act_number}"

    def _act_delete_payment_comment(self, act_number: str) -> str:
        deleted_at = datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M")
        return f"Удален при удалении акта {act_number} {deleted_at}"

    def _create_act_payment(
        self,
        act: Act,
        rows: ActMedServiceRepository,
        payments: PaymentRepository,
        current_user: User,
    ) -> Payment:
        amount = self._act_total(rows.list_for_act(act.id))
        if amount <= 0:
            raise ValidationError("Act payment amount must be positive.")
        return payments.create(
            contract=act.contract,
            user=current_user,
            date=act.date,
            amount=amount,
            comments=self._payment_comment(act.number),
        )

    def _act_total(self, rows: list[ActMedService]) -> Decimal:
        total = Decimal("0")
        for row in rows:
            price = Decimal(str(row.price or 0))
            count = Decimal(str(row.count or 0))
            discount = Decimal(str(row.discount or 0))
            total += price * count * (Decimal("1") - discount / Decimal("100"))
        return total

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
