"""
REST API package for the CRM.

Provides a versioned JSON API under /api with OpenAPI/Swagger docs.
Uses flask-smorest + marshmallow for validation and serialization.
"""
from flask_smorest import Api

def init_api(app):
    """Configure OpenAPI/Swagger and register all REST resources under /api."""
    app.config.setdefault("API_TITLE", "CRM API")
    app.config.setdefault("API_VERSION", "v1")
    app.config.setdefault("OPENAPI_VERSION", "3.0.3")
    app.config.setdefault("OPENAPI_URL_PREFIX", "/api/docs")
    app.config.setdefault("OPENAPI_SWAGGER_UI_PATH", "/swagger-ui")
    app.config.setdefault(
        "OPENAPI_SWAGGER_UI_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )

    api = Api(app)

    from app.api.resources.customers import blp as customers_blp
    from app.api.resources.orders import blp as orders_blp
    from app.api.resources.contacts import blp as contacts_blp

    api.register_blueprint(customers_blp, url_prefix="/api")
    api.register_blueprint(orders_blp, url_prefix="/api")
    api.register_blueprint(contacts_blp, url_prefix="/api")

    return api