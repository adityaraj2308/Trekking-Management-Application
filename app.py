# app.py
# main file - I run this to start the app
# python app.py

from flask import Flask
from flask_login import LoginManager
import os

from database import db, init_db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "trek_secret_key_change_me"

    # sqlite db will be created in same folder
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(base_dir, "trekking.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    # login manager setup
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(int(uid))

    # register blueprints
    from controllers.auth import auth_bp
    from controllers.admin import admin_bp
    from controllers.staff import staff_bp
    from controllers.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(user_bp, url_prefix="/user")

    # create tables + admin
    init_db(app)

    return app


if __name__ == "__main__":
    app = create_app()
    # host 0.0.0.0 so it also works inside container for testing
    app.run(host="0.0.0.0", port=5000, debug=True)
