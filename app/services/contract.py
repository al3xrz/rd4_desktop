from __future__ import annotations

from decimal import Decimal

from app.core.database import session_scope
from app.models import Contract, Payment, User
from app.repositories import ContractRepository, PaymentRepository
from app.services.exceptions import BusinessRuleError, DuplicateError, NotFoundError


class ContractService:
    def create_contract(self, data: dict, current_user: User | None = None) -> Contract:
        payments_data = data.pop("payments", [])

        with session_scope() as session:
            contracts = ContractRepository(session)
            if contracts.get_by_number(data["contract_number"]):
                raise DuplicateError(f"Contract already exists: {data['contract_number']}")

            if current_user is not None:
                current_user = session.merge(current_user)
                data.setdefault("created_by_user", current_user)

            contract = contracts.create(**data)
            payments = PaymentRepository(session)
            payment_date = contract.contract_date

            for amount, comment in self._prepayments_from_contract(data):
                payments.create(
                    contract=contract,
                    date=payment_date,
                    amount=amount,
                    comments=comment,
                    user=current_user,
                )

            for payment in payments_data:
                payments.create(contract=contract, user=current_user, **payment)

            return contract

    def update_contract(self, contract_id: int, data: dict, current_user: User | None = None) -> Contract:
        with session_scope() as session:
            contracts = ContractRepository(session)
            contract = contracts.get(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")

            self._reject_changed_prepayment(data, "prepay_inpatient_treatment", contract.prepay_inpatient_treatment)
            self._reject_changed_prepayment(data, "prepay_childbirth", contract.prepay_childbirth)

            data.pop("payments", None)
            if current_user is not None:
                data["updated_by_user"] = session.merge(current_user)

            updated = contracts.update(contract_id, data)
            if updated is None:
                raise NotFoundError(f"Contract not found: {contract_id}")
            return updated

    def delete_contract(self, contract_id: int, current_user: User | None = None) -> None:
        with session_scope() as session:
            contract = ContractRepository(session).get_with_details(contract_id, include_deleted=True)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")
            if contract.deleted:
                return

            contract.deleted = True
            for payment in contract.payments:
                payment.deleted = True
            for act in contract.acts:
                act.deleted = True
                for row in act.services:
                    row.deleted = True

    def get_contract(self, contract_id: int) -> Contract:
        with session_scope() as session:
            contract = ContractRepository(session).get_with_details(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")
            return contract

    def list_contracts(self, filters: dict | None = None) -> list[Contract]:
        with session_scope() as session:
            return ContractRepository(session).list(limit=None, **(filters or {}))

    def list_contract_summaries(self, include_deleted: bool = False) -> dict[int, dict]:
        with session_scope() as session:
            return ContractRepository(session).list_summaries(include_deleted=include_deleted)

    def get_contract_summary(self, contract_id: int) -> dict:
        with session_scope() as session:
            contract = ContractRepository(session).get_with_details(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")

            services_total = Decimal("0")
            for act in contract.acts:
                if act.deleted:
                    continue
                for row in act.services:
                    if not row.deleted:
                        services_total += row.price * row.count * (Decimal("1") - row.discount / Decimal("100"))

            payments_total = sum(
                (payment.amount for payment in contract.payments if payment.posted and not payment.deleted),
                Decimal("0"),
            )
            refunds_total = sum(
                (payment.amount for payment in contract.payments if payment.posted and not payment.deleted and payment.amount < 0),
                Decimal("0"),
            )
            balance = payments_total - services_total
            status = "paid"
            if balance < 0:
                status = "debt"
            elif balance > 0:
                status = "overpaid"

            return {
                "services_total": services_total,
                "payments_total": payments_total,
                "refunds_total": refunds_total,
                "balance": balance,
                "status": status,
            }

    def _prepayments_from_contract(self, data: dict) -> list[tuple[Decimal, str]]:
        result = []
        inpatient = self._as_decimal(data.get("prepay_inpatient_treatment"))
        childbirth = self._as_decimal(data.get("prepay_childbirth"))
        if inpatient:
            result.append((inpatient, "Предоплата: стационарное лечение"))
        if childbirth:
            result.append((childbirth, "Предоплата: родоразрешение"))
        return result

    def _as_decimal(self, value) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    def _reject_changed_prepayment(self, data: dict, key: str, current_value) -> None:
        if key not in data:
            return
        if self._as_decimal(data[key]) != self._as_decimal(current_value):
            raise BusinessRuleError("Prepayments cannot be changed after contract creation.")
        data.pop(key, None)
