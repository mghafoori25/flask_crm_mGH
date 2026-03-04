"""
Order API endpoints (CRUD + filtering + pagination).
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy import func

from app import db
from app.models import Order, Customer
from app.api.schemas import OrderSchema, OrderUpdateSchema, PaginationQuerySchema
from app.api.resources import require_login, require_role
from flask import request

blp = Blueprint("orders", "orders", url_prefix="/api/orders", description="Orders")


@blp.route("/")
class OrdersCollection(MethodView):

    @blp.arguments(PaginationQuerySchema, location="query")
    @blp.response(200, OrderSchema(many=True))
    def get(self, args):
        """List orders (optional ?q=... or ?customer_id=...)."""
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
        items = query.order_by(Order.order_date.desc()) \
                     .paginate(page=page, per_page=per_page, error_out=False)
        return items.items

    @blp.arguments(OrderSchema)
    @blp.response(201, OrderSchema)
    def post(self, data):
        """Create order."""
        require_role("CHEF")
        # Customer exists?
        Customer.query.get_or_404(data["customer_id"])

        o = Order(**data)
        db.session.add(o)
        db.session.commit()
        return o


@blp.route("/<int:order_id>")
class OrderItem(MethodView):

    @blp.response(200, OrderSchema)
    def get(self, order_id):
        require_login()
        return Order.query.get_or_404(order_id)

    @blp.arguments(OrderUpdateSchema)
    @blp.response(200, OrderSchema)
    def patch(self, data, order_id):
        require_role("CHEF")
        o = Order.query.get_or_404(order_id)
        for k, v in data.items():
            setattr(o, k, v)
        db.session.commit()
        return o

    def delete(self, order_id):
        require_role("CHEF")
        o = Order.query.get_or_404(order_id)
        db.session.delete(o)
        db.session.commit()
        return {"status": "deleted"}, 200