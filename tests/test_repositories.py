from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from tests.test_models_smoke import configure_temp_database


def create_contract_payload(now, user):
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
        "created_by_user": user,
    }


def test_repositories_create_list_and_find_entities(tmp_path, monkeypatch):
    database = configure_temp_database(tmp_path, monkeypatch)

    from app.models import ActMedService, Role
    from app.repositories import (
        ActRepository,
        ContractRepository,
        MedServiceRepository,
        PaymentRepository,
        UserRepository,
    )

    now = datetime.now(timezone.utc)

    with database.create_session() as session:
        users = UserRepository(session)
        contracts = ContractRepository(session)
        payments = PaymentRepository(session)
        acts = ActRepository(session)
        services = MedServiceRepository(session)

        user = users.create(username="admin", name="Admin", hashed_password="hash", role=Role.ADMIN)
        contract = contracts.create(**create_contract_payload(now, user))
        payment = payments.create(contract=contract, date=now, amount=Decimal("150.00"), user=user)
        folder = services.create(is_folder=True, name="Root", unit="", price=0, vat=0)
        med_service = services.create(
            code="A01",
            parent=folder,
            is_folder=False,
            name="Consultation",
            unit="шт",
            price=Decimal("100.00"),
            vat=0,
        )
        act = acts.create(number="A-001", contract=contract, user=user, date=now)
        session.add(
            ActMedService(
                act=act,
                med_service=med_service,
                current_code=med_service.code,
                current_name=med_service.name,
                unit=med_service.unit,
                price=med_service.price,
            )
        )
        session.commit()

        contract_id = contract.id
        payment_id = payment.id

    with database.create_session() as session:
        contracts = ContractRepository(session)
        payments = PaymentRepository(session)
        acts = ActRepository(session)
        services = MedServiceRepository(session)

        contract = contracts.get_by_number("C-001")
        assert contract is not None
        assert contract.id == contract_id
        assert payments.list_for_contract(contract.id)[0].id == payment_id
        assert acts.get_by_number("A-001") is not None
        assert services.get_tree()[0].children[0].name == "Consultation"


def test_repositories_do_not_commit_implicitly(tmp_path, monkeypatch):
    database = configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.repositories import ContractRepository, UserRepository

    now = datetime.now(timezone.utc)

    with database.create_session() as session:
        user = UserRepository(session).create(
            username="admin",
            name="Admin",
            hashed_password="hash",
            role=Role.ADMIN,
        )
        ContractRepository(session).create(**create_contract_payload(now, user))
        session.rollback()

    with database.create_session() as session:
        assert UserRepository(session).get_by_username("admin") is None
        assert ContractRepository(session).get_by_number("C-001") is None


def test_soft_delete_hides_deleted_rows_by_default(tmp_path, monkeypatch):
    database = configure_temp_database(tmp_path, monkeypatch)

    from app.models import Role
    from app.repositories import ContractRepository, UserRepository

    now = datetime.now(timezone.utc)

    with database.create_session() as session:
        user = UserRepository(session).create(
            username="admin",
            name="Admin",
            hashed_password="hash",
            role=Role.ADMIN,
        )
        contract = ContractRepository(session).create(**create_contract_payload(now, user))
        session.commit()
        contract_id = contract.id

    with database.create_session() as session:
        contracts = ContractRepository(session)
        assert contracts.soft_delete(contract_id) is True
        session.commit()

    with database.create_session() as session:
        contracts = ContractRepository(session)
        assert contracts.get(contract_id) is None
        assert contracts.get(contract_id, include_deleted=True) is not None
