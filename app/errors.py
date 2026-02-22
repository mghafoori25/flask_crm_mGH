"""
Custom error handlers (404, 500).
"""

from flask import render_template
from app import db


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