from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.core.paths import get_resource_path
from app.services.act import ActService
from app.services.contract import ContractService
from app.services.exceptions import BusinessRuleError


RU_MONTHS = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

TEMPLATE_DIR = get_resource_path("app", "templates", "docx")


class DocxService:
    def __init__(
        self,
        contract_service: ContractService | None = None,
        act_service: ActService | None = None,
    ) -> None:
        self.contract_service = contract_service or ContractService()
        self.act_service = act_service or ActService()

    def render_paid_contract(self, contract_id: int) -> Path:
        contract = self.contract_service.get_contract(contract_id)
        context = build_contract_context(contract)
        return self._render_template("contract_paid_template.docx", context, f"contract_{contract.contract_number}.docx")

    def render_foms_contract(self, contract_id: int) -> Path:
        contract = self.contract_service.get_contract(contract_id)
        context = build_foms_contract_context(contract)
        return self._render_template("contract_foms_template.docx", context, f"contract_foms_{contract.contract_number}.docx")

    def render_act_ticket(self, act_id: int) -> Path:
        act = self.act_service.get_act(act_id)
        context = build_act_ticket_context(act)
        return self._render_template("ticket_2up_compact.docx", context, f"act_ticket_{act.number}.docx")

    def open_document(self, path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
            return
        subprocess.Popen(["xdg-open", str(path)])

    def _render_template(self, template_name: str, context: dict[str, Any], filename: str) -> Path:
        try:
            from docxtpl import DocxTemplate
        except ImportError as exc:
            raise BusinessRuleError("Для печати DOCX установите зависимость docxtpl.") from exc

        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            raise BusinessRuleError(f"Не найден шаблон DOCX: {template_path}")

        output_dir = Path(tempfile.gettempdir()) / "rd4"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / _safe_filename(filename)

        doc = DocxTemplate(str(template_path))
        doc.render(context)
        doc.save(str(output_path))
        return output_path


def build_contract_context(contract: Any) -> dict[str, Any]:
    contract_day, contract_month, contract_year = date_parts_ru(contract.contract_date)
    patient_birth_day, patient_birth_month, patient_birth_year = date_parts_ru(contract.patient_birth_date)
    delegate_birth_day, delegate_birth_month, delegate_birth_year = date_parts_ru(contract.delegate_birth_date)

    patient_passport = build_passport_lines(
        contract.patient_passport_issued_by,
        contract.patient_passport_issued_code,
        contract.patient_passport_series,
        contract.patient_passport_date,
    )
    delegate_passport = build_passport_lines(
        contract.delegate_passport_issued_by,
        contract.delegate_passport_issued_code,
        contract.delegate_passport_series,
        contract.delegate_passport_date,
    )

    return {
        "contract_number": contract.contract_number,
        "contract_day": contract_day,
        "contract_month": contract_month,
        "contract_year": contract_year,
        "patient_name": contract.patient_name,
        "patient_name_l1": split_line(contract.patient_name, 42, 0),
        "patient_name_l2": split_line(contract.patient_name, 42, 1),
        "patient_birth_day": patient_birth_day,
        "patient_birth_month": patient_birth_month,
        "patient_birth_year": patient_birth_year,
        "patient_reg_address_l1": split_line(contract.patient_reg_address, 42, 0),
        "patient_reg_address_l2": split_line(contract.patient_reg_address, 42, 1),
        "patient_reg_address_l3": split_line(contract.patient_reg_address, 42, 2),
        "patient_live_address_l1": split_line(contract.patient_live_address, 42, 0),
        "patient_live_address_l2": split_line(contract.patient_live_address, 42, 1),
        "patient_live_address_l3": split_line(contract.patient_live_address, 42, 2),
        "patient_phone": contract.patient_phone or "",
        "patient_passport_l1": patient_passport[0],
        "patient_passport_l2": patient_passport[1],
        "patient_passport_l3": patient_passport[2],
        "patient_passport_l4": patient_passport[3],
        "delegate_name_l1": split_line(contract.delegate_name, 42, 0),
        "delegate_name_l2": split_line(contract.delegate_name, 42, 1),
        "delegate_birth_day": delegate_birth_day,
        "delegate_birth_month": delegate_birth_month,
        "delegate_birth_year": delegate_birth_year,
        "delegate_reg_address_l1": split_line(contract.delegate_reg_address, 42, 0),
        "delegate_reg_address_l2": split_line(contract.delegate_reg_address, 42, 1),
        "delegate_reg_address_l3": split_line(contract.delegate_reg_address, 42, 2),
        "delegate_live_address_l1": split_line(contract.delegate_live_address, 42, 0),
        "delegate_live_address_l2": split_line(contract.delegate_live_address, 42, 1),
        "delegate_live_address_l3": split_line(contract.delegate_live_address, 42, 2),
        "delegate_phone": contract.delegate_phone or "",
        "delegate_passport_l1": delegate_passport[0],
        "delegate_passport_l2": delegate_passport[1],
        "delegate_passport_l3": delegate_passport[2],
        "delegate_passport_l4": delegate_passport[3],
        "inpatient_mark": "V" if contract.inpatient_treatment else "",
        "childbirth_mark": "V" if contract.childbirth else "",
        "prepay_inpatient_mark": "V" if as_decimal(contract.prepay_inpatient_treatment) > 0 else "",
        "prepay_childbirth_mark": "V" if as_decimal(contract.prepay_childbirth) > 0 else "",
        "prepay_inpatient_amount": money_ru(contract.prepay_inpatient_treatment),
        "prepay_childbirth_amount": money_ru(contract.prepay_childbirth),
    }


def build_foms_contract_context(contract: Any) -> dict[str, Any]:
    contract_day, contract_month, contract_year = date_parts_ru(contract.contract_date)
    return {
        "contract_number": contract.contract_number,
        "contract_day": contract_day,
        "contract_month": contract_month,
        "contract_year": contract_year,
        "patient_name": contract.patient_name,
        "patient_reg_address": contract.patient_reg_address,
        "patient_phone": contract.patient_phone or "",
        "insurance_number": contract.service_insurance_number or "",
        "patient_passport_full": "; ".join(
            part for part in build_passport_lines(
                contract.patient_passport_issued_by,
                contract.patient_passport_issued_code,
                contract.patient_passport_series,
                contract.patient_passport_date,
            )
            if part
        ),
    }


def build_act_ticket_context(act: Any) -> dict[str, Any]:
    rows = [row for row in act.services if not row.deleted]
    if len(rows) > 8:
        raise BusinessRuleError("В талоне можно напечатать не более 8 услуг.")

    total = Decimal("0")
    context = {
        "org_name": "ООО «Родильный дом №4»",
        "org_addr": "г. Махачкала, ул. М. Ярагского, д. 6",
        "act_number": act.number,
        "act_date_ru": date_ru(act.date),
        "patient_name": act.contract.patient_name if act.contract else "",
    }

    for index in range(8):
        if index < len(rows):
            row = rows[index]
            line_total = row.price * row.count * (Decimal("1") - row.discount / Decimal("100"))
            total += line_total
            values = {
                "code": row.current_code or str(index + 1),
                "name": row.current_name,
                "unit_price": money_int(row.price),
                "count": str(row.count),
                "total": money_int(line_total),
            }
        else:
            values = {"code": "", "name": "", "unit_price": "", "count": "", "total": ""}

        number = index + 1
        for key, value in values.items():
            context[f"s{number}_{key}"] = value

    context["total_rub"] = money_int(total)
    context["total_words"] = f"({money_int(total)} рублей 00 копеек)"
    return context


def date_parts_ru(value: datetime | None) -> tuple[str, str, str]:
    if value is None:
        return "", "", ""
    return f"{value.day:02d}", RU_MONTHS.get(value.month, str(value.month)), str(value.year)


def date_ru(value: datetime | None) -> str:
    if value is None:
        return ""
    return f"«{value.day}» {RU_MONTHS.get(value.month, str(value.month))} {value.year} г"


def build_passport_lines(issued_by: Any, issued_code: Any, series: Any, issued_date: Any) -> list[str]:
    issued_date_text = ""
    if issued_date:
        issued_date_text = f"{issued_date.day:02d}.{issued_date.month:02d}.{issued_date.year}"
    text = "; ".join(
        part
        for part in [
            f"Серия/номер: {series or ''}",
            f"Кем выдан: {issued_by or ''}",
            f"Код подразделения: {issued_code or ''}",
            f"Дата выдачи: {issued_date_text}",
        ]
        if part.split(": ", 1)[1]
    )
    lines = split_lines(text, 58, 4)
    return lines


def split_lines(value: Any, max_len: int, max_lines: int) -> list[str]:
    text = " ".join(str(value or "").split())
    if not text:
        return [""] * max_lines

    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_len:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines] + [""] * (max_lines - len(lines))


def split_line(value: Any, max_len: int, index: int) -> str:
    return split_lines(value, max_len, index + 1)[index]


def as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def money_ru(value: Any) -> str:
    amount = as_decimal(value)
    if amount <= 0:
        return "0"
    return f"{amount.quantize(Decimal('0.01')):.2f}".replace(".", ",")


def money_int(value: Any) -> str:
    return str(int(round(float(as_decimal(value)))))


def _safe_filename(filename: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in filename)
