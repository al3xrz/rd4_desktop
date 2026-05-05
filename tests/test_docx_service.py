from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from tests.test_models_smoke import configure_temp_database
from tests.test_services_smoke import contract_payload


def test_docx_contract_context_contains_template_fields(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services import AuthService, ContractService
    from app.services.docx import build_contract_context, build_foms_contract_context

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
    payload = contract_payload(now)
    payload["service_insurance_number"] = "INS-001"
    contract = ContractService().create_contract(payload, admin)

    context = build_contract_context(contract)
    foms_context = build_foms_contract_context(contract)

    assert context["contract_number"] == "C-001"
    assert context["patient_name"] == "Patient"
    assert context["prepay_inpatient_mark"] == "V"
    assert foms_context["insurance_number"] == "INS-001"
    assert "Серия/номер" in foms_context["patient_passport_full"]


def test_docx_act_ticket_rejects_more_than_eight_services(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services import ActService, AuthService, ContractService, MedServiceService
    from app.services.docx import build_act_ticket_context
    from app.services.exceptions import BusinessRuleError

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
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
    act = ActService().create_act(
        contract.id,
        {
            "number": "A-001",
            "date": now,
            "services": [{"med_service_id": service.id} for _ in range(9)],
        },
        admin,
    )
    act = ActService().get_act(act.id)

    with pytest.raises(BusinessRuleError):
        build_act_ticket_context(act)
