"""
Central validation helpers for server-side input checks.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class DateRangeResult:
    """Result of parsing and validating a date range."""
    from_date: Optional[date]
    to_date: Optional[date]
    error: Optional[str]


def parse_date_range(from_str: str, to_str: str) -> DateRangeResult:
    """
    Parse and validate a date range in format YYYY-MM-DD.
    """
    from_str = (from_str or "").strip()
    to_str = (to_str or "").strip()

    if not from_str and not to_str:
        return DateRangeResult(None, None, None)

    if not from_str or not to_str:
        return DateRangeResult(None, None, "Bitte Start- und Enddatum angeben.")

    try:
        from_date = datetime.strptime(from_str, "%Y-%m-%d").date()
        to_date = datetime.strptime(to_str, "%Y-%m-%d").date()
    except ValueError:
        return DateRangeResult(None, None, "Ungültiges Datum.")

    if from_date > to_date:
        return DateRangeResult(None, None, "Startdatum darf nicht nach Enddatum sein.")

    return DateRangeResult(from_date, to_date, None)


def normalize_email(value: str) -> str:
    """Normalize email for comparisons."""
    return (value or "").strip().lower()


def is_valid_email(value: str) -> bool:
    """Minimal email validation."""
    value = normalize_email(value)
    return bool(value) and "@" in value and "." in value


def safe_text(value: str, max_len: int = 255) -> str:
    """Trim and cut a text field to avoid DB errors."""
    value = (value or "").strip()
    return value[:max_len]