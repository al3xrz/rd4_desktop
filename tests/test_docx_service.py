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


def test_docx_context_keeps_long_fields_for_word_wrapping(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services import ActService, AuthService, ContractService, MedServiceService
    from app.services.docx import build_act_context, build_contract_context

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
    payload = contract_payload(now)
    payload["patient_name"] = "Очень Длинная Фамилия Пациента С Длинным Именем И Отчеством Для Проверки Переносов"
    payload["patient_reg_address"] = (
        "Республика Дагестан город Махачкала очень длинная улица с большим названием "
        "дом сорок два корпус три квартира сто двадцать пять"
    )
    payload["patient_live_address"] = payload["patient_reg_address"]
    payload["patient_passport_issued_by"] = (
        "Очень длинное наименование отдела внутренних дел с дополнительным описанием района выдачи паспорта"
    )
    contract = ContractService().create_contract(payload, admin)

    context = build_contract_context(contract)
    assert context["patient_reg_address"].endswith("сто двадцать пять")
    assert "patient_reg_address_l1" not in context
    assert "района выдачи паспорта" in context["patient_passport_full"]

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
        {"number": "A-LONG", "date": now, "services": [{"med_service_id": service.id}]},
        admin,
    )
    act_context = build_act_context(ActService().get_act(act.id))
    assert act_context["patient_reg_address"].endswith("сто двадцать пять")
    assert "patient_reg_address_l1" not in act_context


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
    services = [
        MedServiceService().create_service(
            {
                "parent_id": folder.id,
                "code": f"A{index:02d}",
                "name": f"Consultation {index}",
                "unit": "шт",
                "price": Decimal("100.00"),
                "vat": 0,
            }
        )
        for index in range(9)
    ]
    act = ActService().create_act(
        contract.id,
        {
            "number": "A-001",
            "date": now,
            "services": [{"med_service_id": service.id} for service in services],
        },
        admin,
    )
    act = ActService().get_act(act.id)

    with pytest.raises(BusinessRuleError):
        build_act_ticket_context(act)


def test_docx_render_act_uses_paid_and_foms_templates(tmp_path, monkeypatch):
    configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.services import ActService, AuthService, ContractService, MedServiceService
    from app.services.docx import DocxService

    now = datetime.now(timezone.utc)
    admin = AuthService().create_user({"username": "admin", "password": "secret", "role": Role.ADMIN})
    contracts = ContractService()
    acts = ActService()
    med_services = MedServiceService()

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

    paid_contract = contracts.create_contract(contract_payload(now), admin)
    paid_act = acts.create_act(
        paid_contract.id,
        {
            "number": "A-001",
            "date": now,
            "services": [{"med_service_id": service.id, "discount": Decimal("10.00")}],
        },
        admin,
    )

    foms_payload = contract_payload(now)
    foms_payload["contract_number"] = "C-002"
    foms_payload["service_insurance"] = True
    foms_payload["service_insurance_number"] = "INS-002"
    foms_contract = contracts.create_contract(foms_payload, admin)
    foms_act = acts.create_act(
        foms_contract.id,
        {"number": "A-002", "date": now, "services": [{"med_service_id": service.id}]},
        admin,
    )

    renderer = DocxService()
    paid_path = renderer.render_act(paid_act.id)
    foms_path = renderer.render_act(foms_act.id)

    assert paid_path.exists()
    assert foms_path.exists()

    from zipfile import ZipFile

    with ZipFile(paid_path) as paid_docx:
        assert "Consultation" in paid_docx.read("word/document.xml").decode("utf-8")
    with ZipFile(foms_path) as foms_docx:
        assert "Consultation" in foms_docx.read("word/document.xml").decode("utf-8")
