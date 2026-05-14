from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from tests.test_models_smoke import configure_temp_database


def contract_payload(now):
    return {
        "contract_number": "C-001",
        "contract_date": now,
        "category": "Категория 2",
        "patient_name": "Patient",
        "patient_birth_date": now,
        "patient_reg_address": "Registration address",
        "patient_live_address": "Live address",
        "patient_phone": "+70000000000",
        "patient_passport_issued_by": "Issuer",
        "patient_passport_issued_code": "000-000",
        "patient_passport_series": "0000 000000",
        "patient_passport_date": now,
        "prepay_inpatient_treatment": Decimal("50.00"),
    }


def test_services_full_smoke_scenario(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services import ActService, AuthService, ContractService, MedServiceService, PaymentService

    now = datetime.now(timezone.utc)
    auth = AuthService()
    contracts = ContractService()
    payments = PaymentService()
    acts = ActService()
    med_services = MedServiceService()

    admin = auth.create_user(
        {
            "username": "admin",
            "password": "secret",
            "name": "Admin",
            "role": Role.ADMIN,
        }
    )
    logged_in = auth.login("admin", "secret")

    contract = contracts.create_contract(contract_payload(now), logged_in)
    summary = contracts.get_contract_summary(contract.id)
    assert summary["payments_total"] == Decimal("50.00")
    assert summary["balance"] == Decimal("50.00")
    assert summary["status"] == "overpaid"

    folder = med_services.create_folder({"name": "Root"})
    service = med_services.create_service(
        {
            "parent_id": folder.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )

    act = acts.create_act(
        contract.id,
        {
            "number": "A-001",
            "date": now,
            "services": [{"med_service_id": service.id, "count": 1}],
        },
        admin,
    )
    summary = contracts.get_contract_summary(contract.id)
    assert summary["services_total"] == Decimal("100.00")
    assert summary["payments_total"] == Decimal("50.00")
    assert summary["balance"] == Decimal("-50.00")
    assert summary["status"] == "debt"

    payment = payments.create_payment(contract.id, {"date": now, "amount": Decimal("50.00")}, admin)
    summary = contracts.get_contract_summary(contract.id)
    assert summary["balance"] == Decimal("0.00")
    assert summary["status"] == "paid"

    payments.unpost_payment(payment.id, "Mistake", admin)
    summary = contracts.get_contract_summary(contract.id)
    assert summary["balance"] == Decimal("-50.00")

    payments.create_refund(contract.id, {"date": now, "amount": Decimal("10.00")}, admin)
    summary = contracts.get_contract_summary(contract.id)
    assert summary["refunds_total"] == Decimal("-10.00")
    assert summary["balance"] == Decimal("-60.00")
    assert contracts.list_contract_summaries()[contract.id]["balance"] == summary["balance"]

    act_with_service = acts.list_acts(contract.id)[0]
    assert act_with_service.number == act.number


def test_services_enforce_business_rules(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services import ActService, AuthService, ContractService, MedServiceService
    from app.services.exceptions import BusinessRuleError

    now = datetime.now(timezone.utc)
    auth = AuthService()
    admin = auth.create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
    contract = ContractService().create_contract(contract_payload(now), admin)
    folder = MedServiceService().create_folder({"name": "Root"})

    with pytest.raises(BusinessRuleError):
        ContractService().update_contract(
            contract.id,
            {"prepay_inpatient_treatment": Decimal("60.00")},
            admin,
        )

    with pytest.raises(BusinessRuleError):
        ActService().create_act(
            contract.id,
            {"number": "A-001", "date": now, "services": [{"med_service_id": folder.id}]},
            admin,
        )


def test_act_service_rows_merge_same_service_and_discount(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.services import ActService, AuthService, ContractService, MedServiceService

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": "admin"})
    contract = ContractService().create_contract(contract_payload(now), admin)
    folder = MedServiceService().create_folder({"name": "Root"})
    service = MedServiceService().create_service(
        {
            "parent_id": folder.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )
    acts = ActService()
    act = acts.create_act(
        contract.id,
        {
            "number": "A-001",
            "date": now,
            "services": [
                {"med_service_id": service.id, "count": 1, "discount": Decimal("10.00")},
                {"med_service_id": service.id, "count": 2, "discount": Decimal("10.00")},
                {"med_service_id": service.id, "count": 1, "discount": Decimal("5.00")},
            ],
        },
        admin,
    )

    rows = acts.list_service_rows(act.id)
    assert len(rows) == 2
    assert sorted((row.count, row.discount) for row in rows) == [(1, Decimal("5.00")), (3, Decimal("10.00"))]

    acts.add_service(act.id, service.id, {"count": 4, "discount": Decimal("10.00")}, admin)
    rows = acts.list_service_rows(act.id)
    assert len(rows) == 2
    assert sorted((row.count, row.discount) for row in rows) == [(1, Decimal("5.00")), (7, Decimal("10.00"))]


def test_act_number_is_generated_from_contract_number(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.services import ActService, AuthService, ContractService, MedServiceService

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": "admin"})
    contract = ContractService().create_contract(contract_payload(now), admin)
    folder = MedServiceService().create_folder({"name": "Root"})
    service = MedServiceService().create_service(
        {
            "parent_id": folder.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )

    acts = ActService()
    assert acts.next_act_number(contract.id) == "C-001 / 1"
    first_act = acts.create_act(
        contract.id,
        {"date": now, "services": [{"med_service_id": service.id, "count": 1}]},
        admin,
    )
    assert acts.next_act_number(contract.id) == "C-001 / 2"
    second_act = acts.create_act(
        contract.id,
        {"number": "", "date": now, "services": [{"med_service_id": service.id, "count": 1}]},
        admin,
    )

    assert first_act.number == "C-001 / 1"
    assert second_act.number == "C-001 / 2"


def test_act_save_options_create_payment_and_mark_contract_discharged(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.core.database import session_scope
    from app.models import Act, ActMedService, Payment
    from app.services import ActService, AuthService, ContractService, MedServiceService, PaymentService
    from app.services.exceptions import BusinessRuleError

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": "admin"})
    contracts = ContractService()
    contract = contracts.create_contract(contract_payload(now), admin)
    folder = MedServiceService().create_folder({"name": "Root"})
    service = MedServiceService().create_service(
        {
            "parent_id": folder.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )

    act = ActService().create_act(
        contract.id,
        {
            "number": "A-001",
            "date": now,
            "services": [{"med_service_id": service.id, "count": 2, "discount": Decimal("10.00")}],
        },
        admin,
        add_payment=True,
        mark_discharged=True,
    )

    payments = PaymentService().list_payments(contract.id)
    updated_contract = contracts.get_contract(contract.id)
    act_payment = [payment for payment in payments if payment.comments == f"Платеж по акту {act.number}"]
    assert updated_contract.discharged is True
    assert updated_contract.discharge_date == now.replace(tzinfo=None)
    assert len(act_payment) == 1
    assert act_payment[0].amount == Decimal("180.00")
    assert ActService().is_act_paid(act.id) is True

    with pytest.raises(BusinessRuleError):
        ActService().update_act(act.id, {"comments": "edited"}, admin)

    ActService().delete_act(act.id, admin)
    deleted_act = ActService().list_acts(contract.id)[0]
    deleted_payment = [
        payment for payment in PaymentService().list_payments(contract.id) if payment.comments.startswith("Удален при удалении акта")
    ][0]
    assert deleted_act.id == act.id
    assert deleted_act.deleted is True
    assert deleted_payment.deleted is True
    assert deleted_payment.comments.startswith(f"Удален при удалении акта {act.number} ")
    deleted_rows = ActService().list_service_rows(act.id)
    assert deleted_rows
    assert all(row.deleted for row in deleted_rows)

    with session_scope() as session:
        deleted_payments = session.query(Payment).filter(Payment.comments.like(f"Удален при удалении акта {act.number} %")).all()
        rows = session.query(ActMedService).filter_by(act_id=act.id).all()
        assert deleted_payments
        assert all(payment.deleted for payment in deleted_payments)
        assert rows
        assert all(row.deleted for row in rows)
        assert session.get(Act, act.id).deleted is True


def test_existing_act_can_be_paid_once(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.services import ActService, AuthService, ContractService, MedServiceService, PaymentService
    from app.services.exceptions import BusinessRuleError

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": "admin"})
    contract_payload_data = contract_payload(now)
    contract_payload_data["prepay_inpatient_treatment"] = Decimal("0")
    contract = ContractService().create_contract(contract_payload_data, admin)
    folder = MedServiceService().create_folder({"name": "Root"})
    service = MedServiceService().create_service(
        {
            "parent_id": folder.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )

    acts = ActService()
    act = acts.create_act(
        contract.id,
        {
            "number": "A-PAY",
            "date": now,
            "services": [{"med_service_id": service.id, "count": 2, "discount": Decimal("10.00")}],
        },
        admin,
    )

    payment = acts.pay_act(act.id, admin)
    payments = PaymentService().list_payments(contract.id)
    act_payments = [item for item in payments if item.comments == f"Платеж по акту {act.number}"]
    assert payment.amount == Decimal("180.00")
    assert len(act_payments) == 1
    assert acts.is_act_paid(act.id) is True

    with pytest.raises(BusinessRuleError):
        acts.pay_act(act.id, admin)


def test_contract_soft_delete_cascades_to_payments_and_acts(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.core.database import session_scope
    from app.models import Act, ActMedService, Contract, Payment, Role
    from app.services import ActService, AuthService, ContractService, MedServiceService, PaymentService

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
    contracts = ContractService()
    contract = contracts.create_contract(contract_payload(now), admin)
    folder = MedServiceService().create_folder({"name": "Root"})
    service = MedServiceService().create_service(
        {
            "parent_id": folder.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )
    act = ActService().create_act(
        contract.id,
        {"number": "A-001", "date": now, "services": [{"med_service_id": service.id, "count": 1}]},
        admin,
    )
    payment = PaymentService().create_payment(contract.id, {"date": now, "amount": Decimal("100.00")}, admin)

    contracts.delete_contract(contract.id, admin)

    assert contracts.list_contracts() == []
    assert [item.id for item in contracts.list_contracts({"include_deleted": True})] == [contract.id]
    deleted_acts = ActService().list_acts(contract.id)
    assert [item.id for item in deleted_acts] == [act.id]
    assert deleted_acts[0].deleted is True
    with session_scope() as session:
        assert session.get(Contract, contract.id).deleted is True
        assert session.get(Act, act.id).deleted is True
        assert session.get(Payment, payment.id).deleted is True
        rows = session.query(ActMedService).filter_by(act_id=act.id).all()
        assert rows
        assert all(row.deleted for row in rows)


def test_med_service_tree_rules(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.services import MedServiceService
    from app.services.exceptions import BusinessRuleError

    med_services = MedServiceService()
    root = med_services.create_folder({"name": "Root", "unit": "bad", "price": 999, "vat": 20})
    service = med_services.create_service(
        {
            "parent_id": root.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )

    assert root.unit == ""
    assert root.price == 0

    with pytest.raises(BusinessRuleError):
        med_services.create_service(
            {
                "parent_id": service.id,
                "code": "BAD",
                "name": "Bad child",
                "unit": "шт",
                "price": Decimal("1.00"),
                "vat": 0,
            }
        )

    with pytest.raises(BusinessRuleError):
        med_services.update_med_service(root.id, {"parent_id": root.id})


def test_med_service_tree_children_are_available_after_session_close(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.services import MedServiceService

    med_services = MedServiceService()
    root = med_services.create_folder({"name": "Root"})
    child = med_services.create_folder({"name": "Child", "parent_id": root.id})
    service = med_services.create_service(
        {
            "parent_id": child.id,
            "code": "A01",
            "name": "Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )

    tree = med_services.get_tree()

    assert tree[0].children[0].id == child.id
    assert tree[0].children[0].children[0].id == service.id
    assert tree[0].children[0].children[0].children == []
