from __future__ import annotations

import argparse
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.core.database import session_scope
from app.models import MedService


INSERT_PATTERN = re.compile(r"^INSERT INTO public\.med_services VALUES \((.*)\);$")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import med_services rows from a PostgreSQL pg_dump file.")
    parser.add_argument("dump", type=Path)
    args = parser.parse_args()

    rows = _read_rows(args.dump)
    created, updated = _import_rows(rows)
    print(f"imported={len(rows)} created={created} updated={updated}")


def _read_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = INSERT_PATTERN.match(line)
        if not match:
            continue
        values = _parse_values(match.group(1))
        if len(values) != 11:
            raise RuntimeError(f"Unexpected med_services values count: {len(values)}")

        old_id, code, parent_id, name, unit, price, vat, comments, created_at, updated_at, is_folder = values
        rows.append(
            {
                "id": old_id,
                "code": code,
                "parent_id": parent_id,
                "name": name.strip() if isinstance(name, str) else name,
                "unit": "" if is_folder else (unit or "шт"),
                "price": Decimal("0") if is_folder else Decimal(str(price or 0)),
                "vat": 0 if is_folder else float(vat or 0),
                "comments": comments,
                "created_at": created_at,
                "updated_at": updated_at,
                "is_folder": bool(is_folder),
                "deleted": False,
            }
        )
    return rows


def _parse_values(raw: str) -> list:
    values = []
    token = []
    in_string = False
    index = 0

    while index < len(raw):
        char = raw[index]
        if in_string:
            if char == "'":
                if index + 1 < len(raw) and raw[index + 1] == "'":
                    token.append("'")
                    index += 2
                    continue
                in_string = False
                index += 1
                continue
            token.append(char)
            index += 1
            continue

        if char == "'":
            in_string = True
            index += 1
            continue
        if char == ",":
            values.append(_convert("".join(token).strip()))
            token = []
            index += 1
            continue
        token.append(char)
        index += 1

    values.append(_convert("".join(token).strip()))
    return values


def _convert(value: str):
    if value == "NULL":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return Decimal(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} .*\+\d{2}", value):
        return datetime.fromisoformat(value.replace(" ", "T") + ":00")
    return value


def _import_rows(rows: list[dict]) -> tuple[int, int]:
    row_by_id = {row["id"]: row for row in rows}
    created = 0
    updated = 0

    with session_scope() as session:
        for row in rows:
            service = session.get(MedService, row["id"])
            if service is None:
                service = MedService(id=row["id"])
                session.add(service)
                created += 1
            else:
                updated += 1

            service.code = row["code"]
            service.parent_id = None
            service.is_folder = row["is_folder"]
            service.name = row["name"]
            service.unit = row["unit"]
            service.price = row["price"]
            service.vat = row["vat"]
            service.deleted = False
            service.comments = row["comments"]
            service.created_at = row["created_at"]
            service.updated_at = row["updated_at"]

        session.flush()

        for row in rows:
            parent_id = row["parent_id"]
            if parent_id is not None and parent_id not in row_by_id:
                raise RuntimeError(f"Missing parent {parent_id} for med service {row['id']}")
            service = session.get(MedService, row["id"])
            service.parent_id = parent_id

    return created, updated


if __name__ == "__main__":
    main()
