def init_api(app):
    ...
    api = Api(app)

    from app.api.resources.customers import blp as customers_blp
    from app.api.resources.orders import blp as orders_blp
    from app.api.resources.contacts import blp as contacts_blp
    from app.api.resources.auth import blp as auth_blp  # ✅ HIER importieren

    api.register_blueprint(customers_blp)
    api.register_blueprint(orders_blp)
    api.register_blueprint(contacts_blp)
    api.register_blueprint(auth_blp)  # ✅ HIER registrieren

    return api