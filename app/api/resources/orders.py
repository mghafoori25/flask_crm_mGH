"""
Order API endpoints (CRUD + filtering + pagination).
"""
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import func

from app import db
from app.models import Order, Customer
from app.api.schemas import OrderSchema, OrderUpdateSchema, PaginationQuerySchema
from app.api.resources import require_login, require_role

blp = Blueprint("orders", __name__, url_prefix="/api/orders", description="Orders")


@blp.route("/")
class OrdersCollection(MethodView):
    """Collection endpoints for orders."""

    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, OrderSchema(many=True))
    def get(self, args):
        """
        List orders (optional filters via ?q=... or ?customer_id=...).

        Requires login.
        """
        require_login()

        q = (request.args.get("q") or "").strip()
        customer_id = request.args.get("customer_id")

        query = Order.query.join(Customer, Customer.id == Order.customer_id)

        if customer_id:
            query = query.filter(Order.customer_id == int(customer_id))

        if q:
            like = f"%{q}%"
            query = query.filter(
                func.cast(Order.id, db.String).ilike(like)
                | Customer.first_name.ilike(like)
                | Customer.last_name.ilike(like)
            )

        page = args["page"]
        per_page = args["per_page"]
        items = (
            query.order_by(Order.order_date.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return items.items

    @blp.arguments(OrderSchema)
    @blp.response(201, OrderSchema)
    def post(self, data):
        """
        Create a new order.

        Only CHEF can create orders.
        """
        require_role("CHEF")

        # Ensure referenced customer exists
        Customer.query.get_or_404(data["customer_id"])

        o = Order(**data)
        db.session.add(o)
        db.session.commit()
        return o


@blp.route("/<int:order_id>")
class OrderItem(MethodView):
    """Item endpoints for a single order."""

    @blp.response(200, OrderSchema)
    def get(self, order_id):
        """
        Get a single order by id.

        Requires login.
        """
        require_login()
        return Order.query.get_or_404(order_id)

    @blp.arguments(OrderSchema)
    @blp.response(200, OrderSchema)
    def put(self, data, order_id):
        """
        Full update (PUT) of an order.

        Professional CRUD:
        - PUT expects the full resource representation (all required fields).
        - Fields not included are not "partially updated" here; send the full object.

        Only CHEF can update orders.
        """
        require_role("CHEF")
        o = Order.query.get_or_404(order_id)

        # If customer_id is part of the full update, ensure it exists
        Customer.query.get_or_404(data["customer_id"])

        # Full replacement of relevant fields
        o.customer_id = data["customer_id"]
        o.order_date = data["order_date"]
        o.status = data["status"]
        o.total_amount = data["total_amount"]

        db.session.commit()
        return o

    @blp.arguments(OrderUpdateSchema)
    @blp.response(200, OrderSchema)
    def patch(self, data, order_id):
        """
        Partial update (PATCH) of an order.

        Only the provided fields are changed.
        Only CHEF can update orders.
        """
        require_role("CHEF")
        o = Order.query.get_or_404(order_id)

        if "customer_id" in data:
            Customer.query.get_or_404(data["customer_id"])

        for k, v in data.items():
            setattr(o, k, v)

        db.session.commit()
        return o

    @blp.response(200)
    def delete(self, order_id):
        """
        Delete an order.

        Only CHEF can delete orders.
        """
        require_role("CHEF")
        o = Order.query.get_or_404(order_id)
        db.session.delete(o)
        db.session.commit()
        return {"status": "deleted", "id": order_id}