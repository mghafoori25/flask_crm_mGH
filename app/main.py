import csv
import io
from io import StringIO
from datetime import datetime, date
from sqlalchemy import func, or_
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user


from app import db
from app.models import Customer, Order, Contact
from app.utils import role_required

main = Blueprint("main", __name__)

CHANNELS = ["Telefon", "E-Mail", "Meeting", "Chat"]
STATUSES = ["Offen", "Bezahlt", "Storniert"]

@main.route("/")
@login_required
def index():
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
    customers = customer_query.order_by(Customer.last_name.asc(), Customer.first_name.asc()) \
                              .paginate(page=customers_page, per_page=10, error_out=False)

    # --- Orders global search
    q_order = request.args.get("q_order", "").strip()
    orders_page = int(request.args.get("orders_page", 1))

    orders_query = Order.query.join(Customer, Customer.id == Order.customer_id)
    if q_order:
        like = f"%{q_order}%"
        # Suche nach Bestell-ID oder Kunde
        orders_query = orders_query.filter(
            or_(
                func.cast(Order.id, db.String).ilike(like),
                Customer.first_name.ilike(like),
                Customer.last_name.ilike(like),
                func.trim(Customer.first_name + " " + Customer.last_name).ilike(like),
            )
        )
    orders = orders_query.order_by(Order.order_date.desc()) \
                         .paginate(page=orders_page, per_page=10, error_out=False)

    # --- Contacts global filter
    channel = request.args.get("channel", "").strip()
    contacts_page = int(request.args.get("contacts_page", 1))

    contacts_query = Contact.query.join(Customer, Customer.id == Contact.customer_id)
    if channel:
        contacts_query = contacts_query.filter(Contact.channel == channel)

    contacts = contacts_query.order_by(Contact.contact_time.desc()) \
                             .paginate(page=contacts_page, per_page=10, error_out=False)

    return render_template(
        "index.html",
        q=q,
        q_order=q_order,
        channel=channel,
        channels=CHANNELS,
        customers=customers,
        orders=orders,
        contacts=contacts,
        current_user=current_user
    )

@main.route("/customers/<int:customer_id>")
@login_required
def customer_detail(customer_id):
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
    period_error = None

    if from_str and to_str:
        try:
            from_date = datetime.strptime(from_str, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_str, "%Y-%m-%d").date()
            if from_date > to_date:
                period_error = "Startdatum darf nicht nach Enddatum sein."
            else:
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
            period_error = "Ungültiges Datum."

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
        total_revenue=total_revenue,
        revenue_last_year=revenue_last_year,
        period_revenue=period_revenue,
        period_error=period_error,
        from_str=from_str,
        to_str=to_str,
        last_orders=last_orders,
        last_contacts=last_contacts,
        channels=CHANNELS
    )

@main.route("/customers/<int:customer_id>/contacts/new", methods=["POST"])
@login_required
def add_contact(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    channel = request.form.get("channel", "").strip()
    subject = request.form.get("subject", "").strip()
    notes = request.form.get("notes", "").strip()

    if channel not in CHANNELS:
        flash("Ungültiger Kanal.")
        return redirect(url_for("main.customer_detail", customer_id=customer.id))

    ct = Contact(
        customer_id=customer.id,
        user_id=current_user.id,
        channel=channel,
        subject=subject[:255] if subject else None,
        notes=notes if notes else None,
        contact_time=datetime.now()
    )
    db.session.add(ct)
    db.session.commit()
    flash("Kontakt gespeichert.")
    return redirect(url_for("main.customer_detail", customer_id=customer.id))

# BONUS: CSV Export (Chef-only)
@main.route("/customers/<int:customer_id>/orders.csv")
@login_required
@role_required("CHEF")
def export_customer_orders_csv(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.order_date.desc()).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["order_id", "order_date", "status", "total_amount"])

    for o in orders:
        writer.writerow([o.id, o.order_date.strftime("%Y-%m-%d"), o.status, f"{float(o.total_amount):.2f}"])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=customer_{customer.id}_orders.csv"}
    )

# BONUS: Monatsumsatz (Chef-only) - SQLite group by month
@main.route("/dashboard/monthly")
@login_required
@role_required("CHEF")
def monthly_dashboard():
    # SQLite: strftime('%Y-%m', order_date)
    rows = (
        db.session.query(
            func.strftime("%Y-%m", Order.order_date).label("month"),
            func.coalesce(func.sum(Order.total_amount), 0).label("revenue")
        )
        .group_by("month")
        .order_by("month")
        .all()
    )
    return render_template("index.html", monthly_rows=rows)  # optional Anzeige, du kannst später extra Template machen

@app.route("/admin/customers/import", methods=["GET", "POST"])
@login_required
def import_customers():

    if current_user.role != "CHEF":
        flash("Nur CHEF darf CSV importieren.")
        return redirect(url_for("index"))

    result = None

    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            flash("Keine Datei hochgeladen.")
            return redirect(request.url)

        update_existing = bool(request.form.get("update_existing"))

        result = {
            "imported": 0,
            "updated": 0,
            "skipped": 0,
            "errors": []
        }

        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)

        for row in reader:
            name = row.get("name")
            email = row.get("email")

            if not name or not email:
                result["skipped"] += 1
                continue

            existing = Customer.query.filter_by(email=email).first()

            if existing:
                if update_existing:
                    existing.name = name
                    result["updated"] += 1
                else:
                    result["skipped"] += 1
            else:
                new_customer = Customer(name=name, email=email)
                db.session.add(new_customer)
                result["imported"] += 1

        db.session.commit()
        flash("Import abgeschlossen.")

    return render_template("import_customers.html", result=result)