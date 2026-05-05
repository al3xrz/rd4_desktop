from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from random import Random

from app.core.database import session_scope
from app.models import Contract, User


FIRST_NAMES = ["Анна", "Мария", "Елена", "Ольга", "Наталья", "Ирина", "Татьяна", "Светлана"]
LAST_NAMES = ["Иванова", "Петрова", "Сидорова", "Смирнова", "Кузнецова", "Попова", "Васильева", "Новикова"]
MIDDLE_NAMES = ["Алексеевна", "Сергеевна", "Ивановна", "Петровна", "Дмитриевна", "Николаевна"]
CITIES = ["Москва", "Казань", "Самара", "Уфа", "Омск", "Екатеринбург", "Новосибирск", "Ростов-на-Дону"]
STREETS = ["Ленина", "Мира", "Победы", "Садовая", "Школьная", "Советская", "Новая", "Центральная"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate load-test contracts.")
    parser.add_argument("--count", type=int, default=5000)
    parser.add_argument("--prefix", default="LOAD")
    args = parser.parse_args()

    created = generate_contracts(args.count, args.prefix)
    print(f"target={args.count} created={created}")


def generate_contracts(count: int, prefix: str) -> int:
    rng = Random(20260502)
    now = datetime.now(timezone.utc)
    created = 0

    with session_scope() as session:
        user = session.query(User).filter(User.username == "admin").one_or_none()
        existing_numbers = {
            number
            for (number,) in session.query(Contract.contract_number)
            .filter(Contract.contract_number.like(f"{prefix}-%"))
            .all()
        }

        batch = []
        for index in range(1, count + 1):
            number = f"{prefix}-{index:06d}"
            if number in existing_numbers:
                continue
            batch.append(_build_contract(number, index, now, rng, user))
            created += 1

            if len(batch) >= 500:
                session.add_all(batch)
                session.flush()
                batch = []

        if batch:
            session.add_all(batch)

    return created


def _build_contract(number: str, index: int, now: datetime, rng: Random, user: User | None) -> Contract:
    name = f"{rng.choice(LAST_NAMES)} {rng.choice(FIRST_NAMES)} {rng.choice(MIDDLE_NAMES)}"
    city = rng.choice(CITIES)
    street = rng.choice(STREETS)
    contract_date = now - timedelta(days=rng.randint(0, 1200), minutes=rng.randint(0, 1440))
    birth_date = now - timedelta(days=rng.randint(18 * 365, 44 * 365))
    passport_date = now - timedelta(days=rng.randint(30, 15 * 365))
    service_insurance = index % 4 == 0

    return Contract(
        contract_number=number,
        contract_date=contract_date,
        birth_history_number=f"RH-{100000 + index}" if index % 3 else None,
        category=f"Категория {(index % 3) + 1}",
        patient_name=name,
        patient_birth_date=birth_date,
        patient_reg_address=_address(city, street, rng),
        patient_live_address=_address(rng.choice(CITIES), rng.choice(STREETS), rng),
        patient_phone=f"+7{rng.randint(9000000000, 9999999999)}",
        patient_passport_issued_by=rng.choice(["УФМС России", "ГУ МВД России", "ОВД Центрального района"]),
        patient_passport_issued_code=f"{rng.randint(100, 999)}-{rng.randint(100, 999)}",
        patient_passport_series=f"{rng.randint(1000, 9999)} {rng.randint(100000, 999999)}",
        patient_passport_date=passport_date,
        inpatient_treatment=index % 2 == 0,
        childbirth=index % 5 != 0,
        prepay_inpatient_treatment=None,
        prepay_childbirth=None,
        service_payed=not service_insurance,
        service_insurance=service_insurance,
        service_insurance_number=f"POL-{index:08d}" if service_insurance else None,
        discharged=index % 7 == 0,
        discharge_date=contract_date + timedelta(days=5) if index % 7 == 0 else None,
        deleted=False,
        comments="Тестовая запись для проверки скорости" if index % 10 == 0 else None,
        created_by_user=user,
        updated_by_user=user,
    )


def _address(city: str, street: str, rng: Random) -> str:
    return f"г. {city}, ул. {street}, д. {rng.randint(1, 180)}, кв. {rng.randint(1, 250)}"


if __name__ == "__main__":
    main()
