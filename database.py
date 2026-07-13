# database.py
# here I have created db object and init function
# db is created programmatically (not manually in DB browser)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


def init_db(app):
    # this creates all tables from models.py
    with app.app_context():
        # import here so that models are registered
        from models import User
        db.create_all()

        # create default admin only if not present
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            new_admin = User(
                username="admin",
                email="admin@trek.com",
                password=generate_password_hash("admin123"),
                full_name="Super Admin",
                role="admin",
                status="active"
            )
            db.session.add(new_admin)
            db.session.commit()
            print(">> default admin created (admin / admin123)")
