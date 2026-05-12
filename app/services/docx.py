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

    def render_act(self, act_id: int) -> Path:
        act = self.act_service.get_act(act_id)
        template_name = "act_foms_template.docx" if act.contract and act.contract.service_insurance else "act_paid_template.docx"
        context = build_act_context(act)
        return self._render_template(template_name, context, f"act_{act.number}.docx")

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

    patient_passport_full = build_passport_text(
        contract.patient_passport_issued_by,
        contract.patient_passport_issued_code,
        contract.patient_passport_series,
        contract.patient_passport_date,
    )
    delegate_passport_full = build_passport_text(
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
        "patient_birth_day": patient_birth_day,
        "patient_birth_month": patient_birth_month,
        "patient_birth_year": patient_birth_year,
        "patient_reg_address": contract.patient_reg_address,
        "patient_live_address": contract.patient_live_address,
        "patient_phone": contract.patient_phone or "",
        "patient_passport_full": patient_passport_full,
        "delegate_name": contract.delegate_name or "",
        "delegate_birth_day": delegate_birth_day,
        "delegate_birth_month": delegate_birth_month,
        "delegate_birth_year": delegate_birth_year,
        "delegate_reg_address": contract.delegate_reg_address or "",
        "delegate_live_address": contract.delegate_live_address or "",
        "delegate_phone": contract.delegate_phone or "",
        "delegate_passport_full": delegate_passport_full,
        "inpatient_mark": "V" if contract.inpatient_treatment else "",
        "childbirth_mark": "V" if contract.childbirth else "",
        "prepay_inpatient_mark": "V" if as_decimal(contract.prepay_inpatient_treatment) > 0 else "",
        "prepay_childbirth_mark": "V" if as_decimal(contract.prepay_childbirth) > 0 else "",
        "prepay_inpatient_amount": money_ru(contract.prepay_inpatient_treatment),
        "prepay_childbirth_amount": money_ru(contract.prepay_childbirth),
        "prepay_inpatient_amount_words": money_words_ru(contract.prepay_inpatient_treatment),
        "prepay_childbirth_amount_words": money_words_ru(contract.prepay_childbirth),
        "delegate_birth_full": date_ru(contract.delegate_birth_date),
    }


def build_foms_contract_context(contract: Any) -> dict[str, Any]:
    contract_day, contract_month, contract_year = date_parts_ru(contract.contract_date)
    patient_birth_day, patient_birth_month, patient_birth_year = date_parts_ru(contract.patient_birth_date)
    return {
        "contract_number": contract.contract_number,
        "contract_day": contract_day,
        "contract_month": contract_month,
        "contract_year": contract_year,
        "patient_birth_day": patient_birth_day,
        "patient_birth_month": patient_birth_month,
        "patient_birth_year": patient_birth_year,
        "patient_name": contract.patient_name,
        "patient_reg_address": contract.patient_reg_address,
        "patient_phone": contract.patient_phone or "",
        "insurance_number": contract.service_insurance_number or "",
        "patient_passport_full": build_passport_text(
            contract.patient_passport_issued_by,
            contract.patient_passport_issued_code,
            contract.patient_passport_series,
            contract.patient_passport_date,
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


def build_act_context(act: Any) -> dict[str, Any]:
    contract = act.contract
    act_day, act_month, act_year = date_parts_ru(act.date)
    contract_day, contract_month, contract_year = date_parts_ru(contract.contract_date if contract else None)
    patient_birth_day, patient_birth_month, patient_birth_year = date_parts_ru(
        contract.patient_birth_date if contract else None
    )

    rows = []
    total = Decimal("0")
    for index, row in enumerate([item for item in act.services if not item.deleted], start=1):
        discount = as_decimal(row.discount)
        price = as_decimal(row.price)
        count = as_decimal(row.count)
        discounted_price = price * (Decimal("1") - discount / Decimal("100"))
        line_total = discounted_price * count
        total += line_total
        rows.append(
            {
                "number": str(index),
                "name": row.current_name,
                "count": quantity_ru(count),
                "unit": row.unit,
                "price": money_ru(price),
                "discount": percent_ru(discount),
                "discounted_price": money_ru(discounted_price),
                "total": money_ru(line_total),
            }
        )

    prepayment = Decimal("0")
    if contract is not None:
        prepayment = as_decimal(contract.prepay_inpatient_treatment) + as_decimal(contract.prepay_childbirth)
    to_pay = total - prepayment
    if to_pay < Decimal("0"):
        to_pay = Decimal("0")

    passport_full = build_passport_text(
        contract.patient_passport_issued_by if contract else "",
        contract.patient_passport_issued_code if contract else "",
        contract.patient_passport_series if contract else "",
        contract.patient_passport_date if contract else None,
    )

    return {
        "act_number": act.number,
        "act_day": act_day,
        "act_month": act_month,
        "act_year": act_year,
        "contract_number": contract.contract_number if contract else "",
        "contract_day": contract_day,
        "contract_month": contract_month,
        "contract_year": contract_year,
        "patient_name": contract.patient_name if contract else "",
        "patient_birth_day": patient_birth_day,
        "patient_birth_month": patient_birth_month,
        "patient_birth_year": patient_birth_year,
        "patient_reg_address": contract.patient_reg_address if contract else "",
        "patient_live_address": contract.patient_live_address if contract else "",
        "patient_phone": contract.patient_phone if contract else "",
        "patient_passport_full": passport_full,
        "total_amount": money_ru(total),
        "prepayment_amount": money_ru(prepayment),
        "amount_due": money_ru(to_pay),
        "total_amount_words": money_with_words_ru(total),
        "vat_amount": "0,00",
        "services": rows,
    }


def date_parts_ru(value: datetime | None) -> tuple[str, str, str]:
    if value is None:
        return "", "", ""
    return f"{value.day:02d}", RU_MONTHS.get(value.month, str(value.month)), str(value.year)


def date_ru(value: datetime | None) -> str:
    if value is None:
        return ""
    return f"«{value.day}» {RU_MONTHS.get(value.month, str(value.month))} {value.year} г"


def build_passport_text(issued_by: Any, issued_code: Any, series: Any, issued_date: Any) -> str:
    issued_date_text = ""
    if issued_date:
        issued_date_text = f"{issued_date.day:02d}.{issued_date.month:02d}.{issued_date.year}"
    return "; ".join(
        part
        for part in [
            f"Серия/номер: {series or ''}",
            f"Кем выдан: {issued_by or ''}",
            f"Код подразделения: {issued_code or ''}",
            f"Дата выдачи: {issued_date_text}",
        ]
        if part.split(": ", 1)[1]
    )


def normalize_docx_text(value: Any) -> str:
    return " ".join(str(value or "").split())


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


def money_with_words_ru(value: Any) -> str:
    amount = as_decimal(value).quantize(Decimal("0.01"))
    rubles = int(amount)
    kopecks = int((amount - Decimal(rubles)) * Decimal("100"))
    return f"{money_ru(amount)} ({money_words_ru(rubles)} {ruble_word(rubles)} {kopecks:02d} копеек)"


def money_words_ru(value: Any) -> str:
    amount = int(round(float(as_decimal(value))))
    if amount <= 0:
        return "ноль"
    return _number_words_ru(amount)


def ruble_word(value: int) -> str:
    value = abs(value) % 100
    if 11 <= value <= 19:
        return "рублей"
    last = value % 10
    if last == 1:
        return "рубль"
    if 2 <= last <= 4:
        return "рубля"
    return "рублей"


def quantity_ru(value: Any) -> str:
    amount = as_decimal(value)
    if amount == amount.to_integral_value():
        return str(int(amount))
    return f"{amount.quantize(Decimal('0.01')):.2f}".replace(".", ",")


def percent_ru(value: Any) -> str:
    amount = as_decimal(value)
    if amount == 0:
        return "0%"
    if amount == amount.to_integral_value():
        return f"{int(amount)}%"
    return f"{amount.quantize(Decimal('0.01')):.2f}".replace(".", ",") + "%"


def _number_words_ru(number: int) -> str:
    units_male = [
        "",
        "один",
        "два",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    ]
    units_female = [
        "",
        "одна",
        "две",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    ]
    teens = [
        "десять",
        "одиннадцать",
        "двенадцать",
        "тринадцать",
        "четырнадцать",
        "пятнадцать",
        "шестнадцать",
        "семнадцать",
        "восемнадцать",
        "девятнадцать",
    ]
    tens = [
        "",
        "",
        "двадцать",
        "тридцать",
        "сорок",
        "пятьдесят",
        "шестьдесят",
        "семьдесят",
        "восемьдесят",
        "девяносто",
    ]
    hundreds = [
        "",
        "сто",
        "двести",
        "триста",
        "четыреста",
        "пятьсот",
        "шестьсот",
        "семьсот",
        "восемьсот",
        "девятьсот",
    ]

    def triad_words(value: int, female: bool = False) -> list[str]:
        words = []
        words.append(hundreds[value // 100])
        rest = value % 100
        if 10 <= rest <= 19:
            words.append(teens[rest - 10])
        else:
            words.append(tens[rest // 10])
            words.append((units_female if female else units_male)[rest % 10])
        return [word for word in words if word]

    def plural(value: int, forms: tuple[str, str, str]) -> str:
        value = abs(value) % 100
        if 11 <= value <= 19:
            return forms[2]
        last = value % 10
        if last == 1:
            return forms[0]
        if 2 <= last <= 4:
            return forms[1]
        return forms[2]

    parts = []
    millions = number // 1_000_000
    thousands = (number // 1_000) % 1_000
    rest = number % 1_000
    if millions:
        parts.extend(triad_words(millions))
        parts.append(plural(millions, ("миллион", "миллиона", "миллионов")))
    if thousands:
        parts.extend(triad_words(thousands, female=True))
        parts.append(plural(thousands, ("тысяча", "тысячи", "тысяч")))
    if rest:
        parts.extend(triad_words(rest))
    return " ".join(parts)


def _safe_filename(filename: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in filename)
