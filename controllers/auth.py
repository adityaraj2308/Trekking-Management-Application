# auth.py
# login / register / logout routes

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    # if user already logged in, take them to their dashboard
    if current_user.is_authenticated:
        return redirect(url_for("auth.go_dashboard"))
    return render_template("home.html")


@auth_bp.route("/dashboard")
@login_required
def go_dashboard():
    # sends user to correct dashboard based on role
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    elif current_user.role == "staff":
        return redirect(url_for("staff.dashboard"))
    else:
        return redirect(url_for("user.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid username or password", "danger")
            return redirect(url_for("auth.login"))

        # check status
        if user.role == "staff" and user.status == "pending":
            flash("Your account is waiting for admin approval.", "warning")
            return redirect(url_for("auth.login"))
        if user.status == "blacklisted":
            flash("Your account has been blacklisted. Contact admin.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash("Logged in successfully!", "success")
        return redirect(url_for("auth.go_dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register/user", methods=["GET", "POST"])
def register_user():
    return _register_common("trekker")


@auth_bp.route("/register/staff", methods=["GET", "POST"])
def register_staff():
    return _register_common("staff")


def _register_common(role):
    # small helper - both registrations use same fields
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        contact = request.form.get("contact", "").strip()

        # simple checks
        if not username or not email or not password:
            flash("Please fill all required fields.", "warning")
            return redirect(request.url)

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "warning")
            return redirect(request.url)

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return redirect(request.url)

        # for staff, status is pending until admin approves
        # for trekker (user), account is directly active
        status = "pending" if role == "staff" else "active"

        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            full_name=full_name,
            contact=contact,
            role=role,
            status=status
        )
        db.session.add(new_user)
        db.session.commit()

        if role == "staff":
            flash("Registered! Please wait for admin approval before login.", "info")
        else:
            flash("Registration successful. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", role=role)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("auth.home"))
