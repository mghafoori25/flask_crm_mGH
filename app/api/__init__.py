from flask import Blueprint

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Endpoints registrieren
from . import customers, leads  # noqa: E402,F401