from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.core.database import init_database
from app.core.migrations import run_migrations
from app.models import Role
from app.services import ActService, AuthService, ContractService, MedServiceService, PaymentService
from app.services.exceptions import DuplicateError


def run_smoke() -> dict:
    init_database()
    run_migrations()

    now = datetime.now(timezone.utc)
    suffix = now.strftime("%Y%m%d%H%M%S")

    auth = AuthService()
    contracts = ContractService()
    med_services = MedServiceService()
    acts = ActService()
    payments = PaymentService()

    username = f"admin_{suffix}"
    try:
        admin = auth.create_user(
            {
                "username": username,
                "password": "secret",
                "name": "Smoke Admin",
                "role": Role.ADMIN,
            }
        )
    except DuplicateError:
        admin = auth.login(username, "secret")

    contract = contracts.create_contract(
        {
            "contract_number": f"SMOKE-{suffix}",
            "contract_date": now,
            "patient_name": "Smoke Patient",
            "patient_birth_date": now,
            "patient_reg_address": "Registration address",
            "patient_live_address": "Live address",
            "patient_phone": "+70000000000",
            "patient_passport_issued_by": "Issuer",
            "patient_passport_issued_code": "000-000",
            "patient_passport_series": "0000 000000",
            "patient_passport_date": now,
            "prepay_inpatient_treatment": Decimal("50.00"),
        },
        admin,
    )
    folder = med_services.create_folder({"name": f"Smoke Root {suffix}"})
    service = med_services.create_service(
        {
            "parent_id": folder.id,
            "code": f"S-{suffix}",
            "name": "Smoke Consultation",
            "unit": "шт",
            "price": Decimal("100.00"),
            "vat": 0,
        }
    )
    acts.create_act(
        contract.id,
        {
            "number": f"ACT-{suffix}",
            "date": now,
            "services": [{"med_service_id": service.id}],
        },
        admin,
    )
    payments.create_payment(contract.id, {"date": now, "amount": Decimal("50.00")}, admin)
    return contracts.get_contract_summary(contract.id)


def main() -> None:
    summary = run_smoke()
    print(f"RD4 services smoke passed: balance={summary['balance']} status={summary['status']}")


if __name__ == "__main__":
    main()
