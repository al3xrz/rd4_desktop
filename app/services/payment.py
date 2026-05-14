from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import session_scope
from app.models import Payment, User
from app.repositories import ContractRepository, PaymentRepository
from app.services.exceptions import BusinessRuleError, NotFoundError, ValidationError


class PaymentService:
    def create_payment(self, contract_id: int, data: dict, current_user: User) -> Payment:
        amount = Decimal(str(data["amount"]))
        if amount <= 0:
            raise ValidationError("Payment amount must be positive.")
        return self._create(contract_id, data, amount, current_user)

    def create_refund(self, contract_id: int, data: dict, current_user: User) -> Payment:
        amount = Decimal(str(data["amount"]))
        if amount >= 0:
            amount = -amount
        if amount == 0:
            raise ValidationError("Refund amount cannot be zero.")
        return self._create(contract_id, data, amount, current_user)

    def update_payment(self, payment_id: int, data: dict, current_user: User | None = None) -> Payment:
        with session_scope() as session:
            payments = PaymentRepository(session)
            payment = payments.get(payment_id)
            if payment is None:
                raise NotFoundError(f"Payment not found: {payment_id}")
            if not payment.posted:
                raise BusinessRuleError("Unposted payment cannot be edited.")
            updated = payments.update(payment_id, data)
            if updated is None:
                raise NotFoundError(f"Payment not found: {payment_id}")
            return updated

    def unpost_payment(self, payment_id: int, reason: str, current_user: User) -> Payment:
        if not reason:
            raise ValidationError("Unpost reason is required.")

        with session_scope() as session:
            current_user = session.merge(current_user)
            payments = PaymentRepository(session)
            payment = payments.get(payment_id)
            if payment is None:
                raise NotFoundError(f"Payment not found: {payment_id}")
            if not payment.posted:
                raise BusinessRuleError("Payment is already unposted.")
            updated = payments.update(
                payment_id,
                {
                    "posted": False,
                    "unposted_at": datetime.now(timezone.utc),
                    "unposted_by": current_user,
                    "unpost_reason": reason,
                },
            )
            return updated

    def list_payments(self, contract_id: int) -> list[Payment]:
        with session_scope() as session:
            return PaymentRepository(session).list_for_contract(contract_id, include_deleted=True)

    def _create(self, contract_id: int, data: dict, amount: Decimal, current_user: User) -> Payment:
        with session_scope() as session:
            contract = ContractRepository(session).get(contract_id)
            if contract is None:
                raise NotFoundError(f"Contract not found: {contract_id}")
            current_user = session.merge(current_user)
            payload = dict(data)
            payload["amount"] = amount
            payload.setdefault("date", datetime.now(timezone.utc))
            return PaymentRepository(session).create(contract=contract, user=current_user, **payload)
