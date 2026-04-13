"""
JWT authentication endpoints for the REST API.
"""
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import Schema, fields

from app.models import User
from app.api.jwt_utils import create_jwt

blp = Blueprint("api_auth", __name__, url_prefix="/api/auth", description="API Auth")

class TokenRequestSchema(Schema):
    """Request schema for obtaining a JWT token."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class TokenResponseSchema(Schema):
    """Response schema containing the JWT access token."""
    access_token = fields.Str(required=True)
    token_type = fields.Str(required=True)
    expires_minutes = fields.Int(required=True)
    role = fields.Str(required=True)

@blp.route("/token")
class TokenResource(MethodView):
    """Exchange email+password for a JWT access token."""

    @blp.arguments(TokenRequestSchema)
    @blp.response(200, TokenResponseSchema)
    def post(self, data):
        user = User.query.filter_by(email=data["email"].lower().strip()).first()
        if not user or not user.check_password(data["password"]):
            abort(401, message="Invalid credentials")

        token = create_jwt(user.id, user.role)
        return {
            "access_token": token,
            "token_type": "Bearer",
            "expires_minutes": 60,
            "role": user.role,
        }