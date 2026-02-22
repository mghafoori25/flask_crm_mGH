"""
KPI calculations for customers.
"""

from __future__ import annotations
from datetime import date
from sqlalchemy import func
from app import db
from app.models import Order


def total_revenue(customer_id: int) -> float:
    """Return total revenue for a customer."""
    val = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.customer_id == customer_id)
        .scalar()
    )
    return float(val or 0)


def revenue_in_range(customer_id: int, from_date: date, to_date: date) -> float:
    """Return revenue for a customer within a given date range."""
    val = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(
            Order.customer_id == customer_id,
            Order.order_date >= from_date,
            Order.order_date <= to_date,
        )
        .scalar()
    )
    return float(val or 0)