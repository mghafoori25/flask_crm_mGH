import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()

login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app(config_class=Config):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User  # noqa

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import auth
    app.register_blueprint(auth)

    from app.main import main
    app.register_blueprint(main)
    
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    from app.api import init_api
    init_api(app)
    
    return app
