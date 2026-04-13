"""
REST API package for the CRM.

Provides a JSON API under /api with OpenAPI/Swagger docs.
Uses flask-smorest + marshmallow for validation and serialization.
"""
from flask_smorest import Api


def init_api(app):
    """Initialize API, OpenAPI config and register all API blueprints."""
    # OpenAPI / Swagger config
    app.config.setdefault("API_TITLE", "CRM API")
    app.config.setdefault("API_VERSION", "v1")
    app.config.setdefault("OPENAPI_VERSION", "3.0.3")
    app.config.setdefault("OPENAPI_URL_PREFIX", "/api/docs")
    app.config.setdefault("OPENAPI_SWAGGER_UI_PATH", "/swagger-ui")
    app.config.setdefault(
        "OPENAPI_SWAGGER_UI_URL",
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )
    
    app.config.setdefault(
    "API_SPEC_OPTIONS",
    {
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        }
    },
)

    api = Api(app)

    # Register resource blueprints
    from app.api.resources.customers import blp as customers_blp
    from app.api.resources.orders import blp as orders_blp
    from app.api.resources.contacts import blp as contacts_blp
    from app.api.resources.auth import blp as auth_blp

    api.register_blueprint(customers_blp)
    api.register_blueprint(orders_blp)
    api.register_blueprint(contacts_blp)
    api.register_blueprint(auth_blp)

    return api