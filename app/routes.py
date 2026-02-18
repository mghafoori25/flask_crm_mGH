from flask import Blueprint, render_template, request
from datetime import datetime, date
from sqlalchemy import func
from app import db
from app.models import Customer, Order, Contact
from flask_login import login_required

bp = Blueprint("main", __name__)

@bp.route("/")
@login_required
def index():
    return render_template("index.html")
    q = request.args.get("q", "").strip()

    customers = Customer.query
    if q:
        customers = customers.filter(
        (Customer.first_name.ilike(f"%{q}%")) |
        (Customer.last_name.ilike(f"%{q}%")) |
        (Customer.email.ilike(f"%{q}%"))
    )
    customers = customers.order_by(Customer.last_name.asc()).all()


    orders = (
    Order.query
    .order_by(Order.order_date.desc())
    .limit(10)
    .all()
)


    channel = request.args.get("channel", "")

    contacts = Contact.query
    if channel:
        contacts = contacts.filter(Contact.channel == channel)

    contacts = (
    contacts
    .order_by(Contact.contact_time.desc())
    .limit(10)
    .all()
)


    return render_template(
    "index.html",
    customers=customers,
    orders=orders,
    contacts=contacts,
    q=q,
    channel=channel
)


@bp.route("/customers/<int:customer_id>")
@login_required
def customer_detail(customer_id):
    ...

    customer = Customer.query.get_or_404(customer_id)

    total_revenue = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.customer_id == customer.id)
        .scalar()
    )

    today = date.today()
    last_year = today.year - 1
    start_last_year = date(last_year, 1, 1)
    end_last_year = date(last_year, 12, 31)

    revenue_last_year = (
        db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(
            Order.customer_id == customer.id,
            Order.order_date >= start_last_year,
            Order.order_date <= end_last_year
        )
        .scalar()
    )

    from_str = request.args.get("from", "").strip()
    to_str = request.args.get("to", "").strip()
    period_revenue = None

    if from_str and to_str:
        try:
            from_date = datetime.strptime(from_str, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_str, "%Y-%m-%d").date()
            period_revenue = (
                db.session.query(func.coalesce(func.sum(Order.total_amount), 0))
                .filter(
                    Order.customer_id == customer.id,
                    Order.order_date >= from_date,
                    Order.order_date <= to_date
                )
                .scalar()
            )
        except ValueError:
            period_revenue = None

    last_orders = (
        Order.query.filter_by(customer_id=customer.id)
        .order_by(Order.order_date.desc()).limit(10).all()
    )

    last_contacts = (
        Contact.query.filter_by(customer_id=customer.id)
        .order_by(Contact.contact_time.desc()).limit(10).all()
    )

    return render_template(
        "customer_detail.html",
        customer=customer,
        total_revenue=total_revenue,
        revenue_last_year=revenue_last_year,
        period_revenue=period_revenue,
        from_str=from_str,
        to_str=to_str,
        last_orders=last_orders,
        last_contacts=last_contacts
    )
