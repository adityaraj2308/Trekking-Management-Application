# models.py
# here I have written all the database tables using SQLAlchemy
# db object is imported from database.py

from database import db
from flask_login import UserMixin
from datetime import datetime


# common User table (for admin, staff, trekker)
# I used single table because login is common for all
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # stored as hash
    full_name = db.Column(db.String(120))
    contact = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)   # admin / staff / trekker

    # for staff -> pending / approved / blacklisted
    # for trekker -> active / blacklisted
    status = db.Column(db.String(20), default="active")

    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    # relations
    bookings = db.relationship("Booking", backref="trekker", lazy=True)
    assigned_treks = db.relationship("Trek", backref="staff", lazy=True,
                                     foreign_keys="Trek.staff_id")


# Trek table
class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)   # Easy / Moderate / Hard
    duration = db.Column(db.Integer, nullable=False)         # in days
    price = db.Column(db.Float, default=0)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    # Pending / Approved / Open / Closed / Completed
    status = db.Column(db.String(20), default="Pending")

    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="trek", lazy=True)


# Booking table
class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)

    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Booked / Cancelled / Completed
    status = db.Column(db.String(20), default="Booked")

    remarks = db.Column(db.String(200))
