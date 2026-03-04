from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, abort
from sqlalchemy import or_

from app import db
from app.models import Customer
from app.api.schemas import CustomerSchema, CustomerUpdateSchema, PaginationQuerySchema
from app.api.resources import require_login, require_role

blp = Blueprint("customers", __name__, url_prefix="/customers", description="Customers")


@blp.route("/")
class CustomersCollection(MethodView):

    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, CustomerSchema(many=True))
    def get(self, args):
        """List customers (optional search via ?q=...)."""
        require_login()

        q = (request.args.get("q") or "").strip()
        query = Customer.query
        if q:
            like = f"%{q}%"
            query = query.filter(or_(
                Customer.first_name.ilike(like),
                Customer.last_name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
            ))

        page = args["page"]
        per_page = args["per_page"]
        items = query.order_by(Customer.last_name.asc(), Customer.first_name.asc()) \
                     .paginate(page=page, per_page=per_page, error_out=False)
        return items.items

    @blp.arguments(CustomerSchema)
    @blp.response(201, CustomerSchema)
    def post(self, data):
        """Create a new customer."""
        require_role("CHEF")

        existing = Customer.query.filter_by(email=data["email"].lower()).first()
        if existing:
            abort(409, description="Customer with this email already exists")

        c = Customer(
            first_name=data["first_name"].strip(),
            last_name=data["last_name"].strip(),
            email=data["email"].lower().strip(),
            phone=(data.get("phone") or None),
        )
        db.session.add(c)
        db.session.commit()
        return c


@blp.route("/<int:customer_id>")
class CustomerItem(MethodView):

    @blp.response(200, CustomerSchema)
    def get(self, customer_id):
        require_login()
        c = Customer.query.get_or_404(customer_id)
        return c

    @blp.arguments(CustomerUpdateSchema)
    @blp.response(200, CustomerSchema)
    def put(self, data, customer_id):
        require_role("CHEF")
        c = Customer.query.get_or_404(customer_id)

        for key, value in data.items():
            setattr(c, key, value if key != "email" else value.lower())

        db.session.commit()
        return c

    @blp.arguments(CustomerUpdateSchema)
    @blp.response(200, CustomerSchema)
    def patch(self, data, customer_id):
        return self.put(data, customer_id)

    @blp.response(200)
    def delete(self, customer_id):
        require_role("CHEF")
        c = Customer.query.get_or_404(customer_id)
        db.session.delete(c)
        db.session.commit()
        return {"status": "deleted", "id": customer_id}