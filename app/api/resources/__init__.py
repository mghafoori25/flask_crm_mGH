"""
Shared helpers for API resources (auth checks, error formatting).
"""
from flask import abort
from flask_login import current_user


def require_login():
    """Abort with 401 if user is not authenticated."""
    if not current_user.is_authenticated:
        abort(401, description="Authentication required")


def require_role(role: str):
    """Abort with 403 if current user lacks required role."""
    require_login()
    if getattr(current_user, "role", None) != role:
        abort(403, description=f"Requires role {role}")