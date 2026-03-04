"""
Custom error handlers (404, 500).
"""

from flask import render_template
from app import db
from flask import jsonify, request

def register_error_handlers(app):
    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith("/api/"):
            return jsonify(error="unauthorized", message=getattr(e, "description", "Unauthorized")), 401
        return e

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith("/api/"):
            return jsonify(error="forbidden", message=getattr(e, "description", "Forbidden")), 403
        return e

def register_error_handlers(app) -> None:
    """Register custom error pages."""
    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        # rollback in case of broken db transaction
        db.session.rollback()
        return render_template("500.html"), 500