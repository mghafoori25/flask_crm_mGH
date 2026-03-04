"""
Contact API endpoints (CRUD + channel filter + pagination).
"""
from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request
from datetime import datetime

from app import db
from app.models import Contact, Customer
from app.api.schemas import ContactSchema, PaginationQuerySchema
from app.api.resources import require_login
from flask_login import current_user

blp = Blueprint("contacts", __name__, url_prefix="/contacts", description="Contacts")


@blp.route("/")
class ContactsCollection(MethodView):

    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, ContactSchema(many=True))
    def get(self, args):
        """List contacts (optional ?channel=...)."""
        require_login()

        channel = (request.args.get("channel") or "").strip()
        query = Contact.query
        if channel:
            query = query.filter(Contact.channel == channel)

        items = query.order_by(Contact.contact_time.desc()) \
                     .paginate(page=args["page"], per_page=args["per_page"], error_out=False)
        return items.items

    @blp.arguments(ContactSchema)
    @blp.response(201, ContactSchema)
    def post(self, data):
        """Create contact; user_id comes from session."""
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