"""
Contact API endpoints (CRUD + channel filter + pagination).
"""
from datetime import datetime

from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_login import current_user

from app import db
from app.models import Contact, Customer
from app.api.schemas import (
    ContactSchema,
    ContactCreateSchema,
    ContactUpdateSchema,
    PaginationQuerySchema,
)
from app.api.resources import require_login, require_role

blp = Blueprint("contacts", __name__, url_prefix="/api/contacts", description="Contacts")


@blp.route("/")
class ContactsCollection(MethodView):
    """Collection endpoints for contacts."""

    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, ContactSchema(many=True))
    def get(self, args):
        """List contacts (optional ?channel=...). Requires login."""
        require_login()

        channel = (request.args.get("channel") or "").strip()
        query = Contact.query
        if channel:
            query = query.filter(Contact.channel == channel)

        items = (
            query.order_by(Contact.contact_time.desc())
            .paginate(page=args["page"], per_page=args["per_page"], error_out=False)
        )
        return items.items

    @blp.arguments(ContactCreateSchema)
    @blp.response(201, ContactSchema)
    def post(self, data):
        """
        Create contact.
        user_id comes from session, contact_time set server-side.
        Requires login (EMPLOYEE + CHEF).
        """
        require_login()

        Customer.query.get_or_404(data["customer_id"])

        c = Contact(
            customer_id=data["customer_id"],
            user_id=current_user.id,
            channel=data["channel"],
            subject=data.get("subject"),
            notes=data.get("notes"),
            contact_time=datetime.now(),
        )
        db.session.add(c)
        db.session.commit()
        return c


@blp.route("/<int:contact_id>")
class ContactItem(MethodView):
    """Item endpoints for a single contact."""

    @blp.response(200, ContactSchema)
    def get(self, contact_id):
        """Get single contact. Requires login."""
        require_login()
        return Contact.query.get_or_404(contact_id)

    @blp.arguments(ContactCreateSchema)
    @blp.response(200, ContactSchema)
    def put(self, data, contact_id):
        """
        Full update (PUT) of a contact.
        Only CHEF can update.
        """
        require_role("CHEF")
        c = Contact.query.get_or_404(contact_id)

        Customer.query.get_or_404(data["customer_id"])

        c.customer_id = data["customer_id"]
        c.channel = data["channel"]
        c.subject = data.get("subject")
        c.notes = data.get("notes")
        c.contact_time = datetime.now()

        db.session.commit()
        return c

    @blp.arguments(ContactUpdateSchema)
    @blp.response(200, ContactSchema)
    def patch(self, data, contact_id):
        """
        Partial update (PATCH) of a contact.
        Only CHEF can update.
        """
        require_role("CHEF")
        c = Contact.query.get_or_404(contact_id)

        if "customer_id" in data:
            Customer.query.get_or_404(data["customer_id"])

        for k, v in data.items():
            setattr(c, k, v)

        c.contact_time = datetime.now()
        db.session.commit()
        return c

    @blp.response(200)
    def delete(self, contact_id):
        """Delete contact. Only CHEF can delete."""
        require_role("CHEF")
        c = Contact.query.get_or_404(contact_id)
        db.session.delete(c)
        db.session.commit()
        return {"status": "deleted", "id": contact_id}