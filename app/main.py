"""
Main application routes (dashboard, customer detail, import/export).
Implements controller logic of the CRM.
"""

import csv
from io import StringIO
from datetime import datetime, date

from sqlalchemy import func, or_
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user

from app import db
from app.models import Customer, Order, Contact
from app.utils import role_required

from app.validators import parse_date_range
from app.services.kpi_service import total_revenue as kpi_total_revenue, revenue_in_range
from app.services.import_service import import_customers_csv

main = Blueprint("main", __name__)

CHANNELS = ["Telefon", "E-Mail", "Meeting", "Chat"]
STATUSES = ["Offen", "Bezahlt", "Storniert"]


@main.route("/")
@login_required
def index():
    """
    Dashboard view.

    Displays customer search, global orders (chronological)
    and contact overview with optional filtering.
    """
    # --- Customers search
    q = request.args.get("q", "").strip()
    customers_page = int(request.args.get("customers_page", 1))

    customer_query = Customer.query
    if q:
        like = f"%{q}%"
        customer_query = customer_query.filter(
            or_(
                Customer.first_name.ilike(like),
                Customer.last_name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
            )
        )
    customers = (
        customer_query.order_by(Customer.last_name.asc(), Customer.first_name.asc())
        .paginate(page=customers_page, per_page=10, error_out=False)
    )

    # --- Orders global search
    q_order = request.args.get("q_order", "").strip()
    orders_page = int(request.args.get("orders_page", 1))

    orders_query = Order.query.join(Customer, Customer.id == Order.customer_id)
    if q_order:
        like = f"%{q_order}%"
        orders_query = orders_query.filter(
            or_(
                func.cast(Order.id, db.String).ilike(like),
                Customer.first_name.ilike(like),
                Customer.last_name.ilike(like),
                func.trim(Customer.first_name + " " + Customer.last_name).ilike(like),
            )
        )
    orders = (
        orders_query.order_by(Order.order_date.desc())
        .paginate(page=orders_page, per_page=10, error_out=False)
    )

    # --- Contacts global filter
    channel = request.args.get("channel", "").strip()
    contacts_page = int(request.args.get("contacts_page", 1))

    contacts_query = Contact.query.join(Customer, Customer.id == Contact.customer_id)
    if channel:
        contacts_query = contacts_query.filter(Contact.channel == channel)

    contacts = (
        contacts_query.order_by(Contact.contact_time.desc())
        .paginate(page=contacts_page, per_page=10, error_out=False)
    )

    return render_template(
        "index.html",
        q=q,
        q_order=q_order,
        channel=channel,
        channels=CHANNELS,
        customers=customers,
        orders=orders,
        contacts=contacts,
        current_user=current_user,
    )


@main.route("/customers/<int:customer_id>")
@login_required
def customer_detail(customer_id: int):
    """
    Customer detail view.

    Displays revenue KPIs, date range filtering,
    latest orders and latest contacts.
    """
    customer = Customer.query.get_or_404(customer_id)

    # KPI: Umsatz gesamt
    total_rev = kpi_total_revenue(customer.id)

    # KPI: Umsatz letztes Jahr
    today = date.today()
    last_year = today.year - 1
    start_last_year = date(last_year, 1, 1)
    end_last_year = date(last_year, 12, 31)
    rev_last_year = revenue_in_range(customer.id, start_last_year, end_last_year)

    # Datumsbereich (validiert)
    from_str = request.args.get("from", "").strip()
    to_str = request.args.get("to", "").strip()
    period_revenue = None

    dr = parse_date_range(from_str, to_str)
    period_error = dr.error
    if dr.from_date and dr.to_date and not period_error:
        period_revenue = revenue_in_range(customer.id, dr.from_date, dr.to_date)

    last_orders = (
        Order.query.filter_by(customer_id=customer.id)
        .order_by(Order.order_date.desc())
        .limit(10)
        .all()
    )

    last_contacts = (
        Contact.query.filter_by(customer_id=customer.id)
        .order_by(Contact.contact_time.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "customer_detail.html",
        customer=customer,
        total_revenue=total_rev,
        revenue_last_year=rev_last_year,
        period_revenue=period_revenue,
        period_error=period_error,
        from_str=from_str,
        to_str=to_str,
        last_orders=last_orders,
        last_contacts=last_contacts,
        channels=CHANNELS,
    )


@main.route("/customers/<int:customer_id>/contacts/new", methods=["POST"])
@login_required
def add_contact(customer_id: int):
    """
    Creates a new contact entry for a customer.
    Validates input and stores the contact in the database.
    """
    customer = Customer.query.get_or_404(customer_id)

    channel = request.form.get("channel", "").strip()
    subject = request.form.get("subject", "").strip()
    notes = request.form.get("notes", "").strip()

    if channel not in CHANNELS:
        flash("Ungültiger Kanal.", "danger")
        return redirect(url_for("main.customer_detail", customer_id=customer.id))

    ct = Contact(
        customer_id=customer.id,
        user_id=current_user.id,
        channel=channel,
        subject=subject[:255] if subject else None,
        notes=notes[:1000] if notes else None,
        contact_time=datetime.now(),
    )

    db.session.add(ct)
    db.session.commit()
    flash("Kontakt gespeichert.", "success")
    return redirect(url_for("main.customer_detail", customer_id=customer.id))


@main.route("/export/customers.csv")
@login_required
def export_customers_csv():
    """
    Exportiert Kundendaten als Excel-taugliche CSV-Datei (Semikolon, UTF-8-SIG, klare Header).
    Nur für Rolle CHEF.
    """
    if current_user.role != "CHEF":
        flash("Keine Berechtigung für den Export.", "danger")
        return redirect(url_for("main.index"))

    customers = Customer.query.order_by(Customer.id.asc()).all()

    output = StringIO(newline="")
    writer = csv.writer(
        output,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n",
    )

    headers = [
        "ID",
        "Vorname",
        "Nachname",
        "E-Mail",
        "Firma",
        "Telefon",
        "Status",
        "Erstellt am",
    ]
    writer.writerow(headers)

    def safe(value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return str(value)

    for c in customers:
        status_value = getattr(c, "status", "")
        if isinstance(status_value, bool):
            status_value = "AKTIV" if status_value else "INAKTIV"
        elif str(status_value).isdigit():
            status_value = "AKTIV" if str(status_value) == "1" else "INAKTIV"

        created_at = getattr(c, "created_at", None)
        created_at_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else ""

        writer.writerow(
            [
                safe(getattr(c, "id", "")),
                safe(getattr(c, "first_name", "")),
                safe(getattr(c, "last_name", "")),
                safe(getattr(c, "email", "")),
                safe(getattr(c, "company", "")),
                safe(getattr(c, "phone", "")),
                safe(status_value),
                created_at_str,
            ]
        )

    csv_text = output.getvalue()
    csv_bytes = csv_text.encode("utf-8-sig")

    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=customers_export.csv"},
    )


@main.route("/customers/<int:customer_id>/export-orders.csv")
@login_required
def export_customer_orders_csv(customer_id: int):
    """
    Exportiert die Bestellungen eines einzelnen Kunden als CSV.
    Nur für Rolle CHEF.

    Hinweis: Das Template erwartet genau diesen Endpoint-Namen:
    url_for('main.export_customer_orders_csv', customer_id=customer.id)
    """
    if current_user.role != "CHEF":
        flash("Keine Berechtigung für den Export.", "danger")
        return redirect(url_for("main.index"))

    customer = Customer.query.get_or_404(customer_id)

    orders = (
        Order.query.filter_by(customer_id=customer.id)
        .order_by(Order.order_date.desc())
        .all()
    )

    output = StringIO(newline="")
    writer = csv.writer(
        output,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n",
    )

    writer.writerow(
        [
            "Bestell-ID",
            "Kunde",
            "Datum",
            "Status",
            "Gesamtbetrag",
        ]
    )

    customer_name = f"{getattr(customer, 'first_name', '')} {getattr(customer, 'last_name', '')}".strip()

    for o in orders:
        order_date_str = o.order_date.strftime("%Y-%m-%d") if getattr(o, "order_date", None) else ""
        writer.writerow(
            [
                getattr(o, "id", ""),
                customer_name,
                order_date_str,
                getattr(o, "status", ""),
                getattr(o, "total_amount", ""),
            ]
        )

    csv_text = output.getvalue()
    csv_bytes = csv_text.encode("utf-8-sig")

    filename = f"customer_{customer.id}_orders.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@main.route("/dashboard/monthly")
@login_required
@role_required("CHEF")
def monthly_dashboard():
    """
    Generates monthly revenue aggregation.
    Accessible only for CHEF role.
    """
    rows = (
        db.session.query(
            func.strftime("%Y-%m", Order.order_date).label("month"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue"),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    return render_template("index.html", monthly_rows=rows)


@main.route("/admin/customers/import", methods=["GET", "POST"])
@login_required
@role_required("CHEF")
def import_customers():
    """
    Imports customers from a CSV file.
    Performs validation and optional update of existing records.
    """
    result = None

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Bitte eine CSV-Datei auswählen.", "danger")
            return redirect(request.url)

        update_existing = bool(request.form.get("update_existing"))

        try:
            result = import_customers_csv(file.read(), update_existing)
            db.session.commit()
            flash("Import abgeschlossen.", "success")
        except Exception:
            db.session.rollback()
            flash("Import fehlgeschlagen (Serverfehler).", "danger")
            raise

    return render_template("import.html", result=result)