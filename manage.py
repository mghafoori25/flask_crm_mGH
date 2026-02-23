"""
Management script for the CRM application.

Provides command-line interface commands for running the
development server, database migrations and seeding.
"""

import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Customer, Order, Contact

app = create_app()

CHANNELS = ["Telefon", "E-Mail", "Meeting", "Chat"]
STATUSES = ["Offen", "Bezahlt", "Storniert"]

def init_db():
    with app.app_context():
        db.create_all()
        print("DB init OK")

def seed():
    """
    Seeds the database with example data
    (customers, orders, contacts).
    """
    with app.app_context():
        db.drop_all()
        db.create_all()

        chef = User(name="Chef", email="chef@example.com", role="CHEF")
        chef.set_password("chef123")
        emp = User(name="Mitarbeiter", email="emp@example.com", role="ANGESTELLTER")
        emp.set_password("emp123")
        db.session.add_all([chef, emp])
        db.session.commit()

        customers = []
        for i in range(1, 11):
            c = Customer(
                first_name=f"Kunde{i}",
                last_name=f"Test{i}",
                email=f"kunde{i}@example.com",
                phone=f"+43 660 000{i:03d}"
            )
            db.session.add(c)
            customers.append(c)
        db.session.commit()

        now = datetime.now()

        for _ in range(50):
            c = random.choice(customers)
            od = now - timedelta(days=random.randint(0, 365))
            status = random.choice(STATUSES)
            total = round(random.uniform(10, 250), 2)
            db.session.add(Order(customer_id=c.id, order_date=od, status=status, total_amount=total))

        for _ in range(50):
            c = random.choice(customers)
            ct_time = now - timedelta(days=random.randint(0, 365))
            user = random.choice([chef, emp])
            ch = random.choice(CHANNELS)
            db.session.add(Contact(
                customer_id=c.id,
                user_id=user.id,
                channel=ch,
                subject=f"{ch} Kontakt",
                notes="Seed",
                contact_time=ct_time
            ))

        db.session.commit()
        print("Seed OK: 10 Kunden, 50 Bestellungen, 50 Kontakte, 2 Users")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init-db":
        init_db()
    elif cmd == "seed":
        seed()
    else:
        print("Usage:")
        print("  python manage.py init-db")
        print("  python manage.py seed")
