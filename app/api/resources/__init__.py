"""
Shared helpers for API resources (auth checks).

Supports either:
- Session auth (Flask-Login) for the web UI, OR
- JWT Bearer token for the REST API.
"""
from flask import request
from flask_login import current_user
from flask_smorest import abort

from app.api.jwt_utils import decode_jwt


def _jwt_payload_or_none():
    """
    Return decoded JWT payload if Authorization: Bearer <token> is present.
    If the header is missing, returns None.
    If the token is invalid/expired, aborts with 401.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ", 1)[1].strip()
    try:
        return decode_jwt(token)
    except Exception:
        abort(401, message="Invalid or expired token")


def require_login():
    """
    Abort with 401 if neither a valid session nor a valid JWT token is present.
    Returns a payload-like dict with user id and role for optional use.
    """
    # Session auth (works when you logged in via the web UI)
    if current_user.is_authenticated:
        return {"sub": str(current_user.id), "role": getattr(current_user, "role", None)}

    # JWT auth (API clients)
    payload = _jwt_payload_or_none()
    if payload is None:
        abort(401, message="Authentication required")

    return payload


def require_role(role: str):
    """
    Abort with 403 if the current user (session or JWT) lacks the required role.
    Returns the payload.
    """
    payload = require_login()
    if payload.get("role") != role:
        abort(403, message=f"Requires role {role}")
    return payload