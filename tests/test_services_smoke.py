from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from tests.test_models_smoke import configure_temp_database


def contract_payload(now):
    return {
        "contract_number": "C-001",
        "contract_date": now,
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
