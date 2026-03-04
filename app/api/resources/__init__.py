"""
Shared helpers for API resources (auth checks, error formatting).
"""
from flask_login import current_user
from flask_smorest import abort

def require_login():
    """Abort with 401 if the current user is not authenticated."""
    if not current_user.is_authenticated:
        abort(401, message="Authentication required")

def require_role(role: str):
    """Abort with 403 if the current user lacks the required role."""
    require_login()
    if getattr(current_user, "role", None) != role:
        abort(403, message=f"Requires role {role}")