"""
Database models for the CRM application.
Defines User, Customer, Order and Contact entities.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """
    Represents an authenticated system user with a specific role.
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default="ANGESTELLTER")  # CHEF / ANGESTELLTER

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Customer(db.Model):
    """
    Represents a customer in the CRM system.
    Stores personal data and relationships to orders and contacts.
    """
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name  = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(255), unique=True)
    phone      = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="customer", lazy=True, cascade="all, delete-orphan")
    contacts = db.relationship("Contact", backref="customer", lazy=True, cascade="all, delete-orphan")

    def full_name(self):
        
        """
        Returns the full name of the customer.
        """
        
        return f"{self.first_name} {self.last_name}"

class Order(db.Model):
    """
    Represents a customer order.
    Stores order date, status and total amount.
    """
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Offen")  # Offen/Bezahlt/Storniert
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

class Contact(db.Model):
    """
    Represents a communication entry between a user and a customer.
    """
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    channel = db.Column(db.String(20), nullable=False)  # Telefon/E-Mail/Meeting/Chat
    subject = db.Column(db.String(255))
    notes = db.Column(db.Text)
    contact_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="contacts", lazy=True)
