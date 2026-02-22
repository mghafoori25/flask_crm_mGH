"""
CSV import services for customers.
"""

from __future__ import annotations
import csv
import io
from dataclasses import dataclass
from typing import Any

from app import db
from app.models import Customer
from app.validators import normalize_email, is_valid_email, safe_text


@dataclass
class ImportResult:
    """Structured result of a CSV import."""
    imported: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


def _detect_delimiter(text: str) -> str:
    """Detect likely delimiter between ';' and ','."""
    return ";" if text.count(";") > text.count(",") else ","


def import_customers_csv(file_bytes: bytes, update_existing: bool) -> ImportResult:
    """
    Import customers from CSV bytes.

    Required headers: name,email
    Optional: phone

    If update_existing=True, update existing customers (match by email).
    """
    result = ImportResult()

    text = file_bytes.decode("utf-8-sig", errors="replace")
    delimiter = _detect_delimiter(text)

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        result.errors.append({"row": 1, "field": "header", "message": "CSV hat keinen Header", "value": ""})
        return result

    header = {h.strip().lower() for h in reader.fieldnames if h}
    if "name" not in header or "email" not in header:
        result.errors.append({"row": 1, "field": "header", "message": "Spalten 'name' und 'email' fehlen", "value": str(reader.fieldnames)})
        return result

    for line_no, row in enumerate(reader, start=2):
        row_norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}

        name = safe_text(row_norm.get("name", ""), 255)
        email = normalize_email(row_norm.get("email", ""))
        phone = safe_text(row_norm.get("phone", ""), 50) or None

        if not name:
            result.errors.append({"row": line_no, "field": "name", "message": "Pflichtfeld leer", "value": ""})
            result.skipped += 1
            continue

        if not is_valid_email(email):
            result.errors.append({"row": line_no, "field": "email", "message": "Ungültige Email", "value": email})
            result.skipped += 1
            continue

        existing = Customer.query.filter_by(email=email).first()
        if existing:
            if update_existing:
                # Dein CRM nutzt first_name/last_name/email/phone → name wird in first_name gespeichert
                existing.first_name = name
                existing.last_name = existing.last_name or ""
                existing.phone = phone
                result.updated += 1
            else:
                result.skipped += 1
            continue

        db.session.add(Customer(first_name=name, last_name="", email=email, phone=phone))
        result.imported += 1

    return result