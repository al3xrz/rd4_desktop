from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal


def configure_temp_database(tmp_path, monkeypatch):
    data_dir = tmp_path / "rd4-data"
    monkeypatch.setenv("RD4_DATA_DIR", str(data_dir))

    from app.core import config
    from app.core import database
    from app.core import migrations

    current_settings = config.load_settings()
    database.settings = current_settings
    migrations.settings = current_settings
    database.get_engine.cache_clear()
    database.get_session_factory.cache_clear()

    database.init_database()
    migrations.run_migrations()
    return database


def test_models_relationships_smoke(tmp_path, monkeypatch):
    database = configure_temp_database(tmp_path, monkeypatch)

    from app.models import Act, ActMedService, Contract, MedService, Payment, Role, User

    now = datetime.now(timezone.utc)

    with database.create_session() as session:
        user = User(
            username="admin",
            name="Admin",
            hashed_password="hash",
            role=Role.ADMIN,
        )
        service = MedService(
            code="A01",
            is_folder=False,
            name="Consultation",
            unit="шт",
            price=Decimal("100.00"),
            vat=0,
        )
        contract = Contract(
            contract_number="C-001",
            contract_date=now,
            patient_name="Patient",
            patient_birth_date=now,
            patient_reg_address="Registration address",
            patient_live_address="Live address",
            patient_phone="+70000000000",
            patient_passport_issued_by="Issuer",
            patient_passport_issued_code="000-000",
            patient_passport_series="0000 000000",
            patient_passport_date=now,
            created_by_user=user,
        )
        payment = Payment(
            contract=contract,
            date=now,
            amount=Decimal("100.00"),
            user=user,
        )
        act = Act(
            number="A-001",
            contract=contract,
            user=user,
            date=now,
        )
        act_service = ActMedService(
            act=act,
            med_service=service,
            current_code=service.code,
            current_name=service.name,
            unit=service.unit,
            price=service.price,
            count=1,
        )

        session.add_all([user, service, contract, payment, act, act_service])
        session.commit()

        contract_id = contract.id

    with database.create_session() as session:
        contract = session.get(Contract, contract_id)

        assert contract is not None
        assert contract.created_by_user.username == "admin"
        assert len(contract.payments) == 1
        assert contract.payments[0].posted is True
        assert len(contract.acts) == 1
        assert contract.acts[0].services[0].current_name == "Consultation"
