# user.py
# routes for trekker (normal user)

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from database import db
from models import Trek, Booking, User

user_bp = Blueprint("user", __name__)


def trekker_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "trekker":
            abort(403)
        if current_user.status == "blacklisted":
            flash("Your account is blacklisted.", "danger")
            return redirect(url_for("auth.home"))
        return f(*args, **kwargs)
    return wrapper


@user_bp.route("/dashboard")
@login_required
@trekker_only
def dashboard():
    # available treks means status = Open
    available = Trek.query.filter_by(status="Open").all()
    my_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.id.desc()).all()
    return render_template("user/dashboard.html",
                           available=available, my_bookings=my_bookings)


@user_bp.route("/treks")
@login_required
@trekker_only
def treks_list():
    # search + filter
    q = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "")
    location = request.args.get("location", "").strip()

    # show only Approved / Open treks to users (as per problem statement)
    query = Trek.query.filter(Trek.status.in_(["Approved", "Open"]))

    if q:
        query = query.filter(Trek.name.ilike(f"%{q}%"))
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if location:
        query = query.filter(Trek.location.ilike(f"%{location}%"))

    treks = query.all()
    return render_template("user/treks.html", treks=treks,
                           q=q, difficulty=difficulty, location=location)


@user_bp.route("/book/<int:trek_id>", methods=["POST"])
@login_required
@trekker_only
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # only Open treks can be booked
    if trek.status != "Open":
        flash("This trek is not open for booking right now.", "warning")
        return redirect(url_for("user.treks_list"))

    # prevent overbooking
    if trek.available_slots <= 0:
        flash("Sorry, this trek is fully booked!", "danger")
        return redirect(url_for("user.treks_list"))

    # check if user already booked this trek (and not cancelled)
    already = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id) \
        .filter(Booking.status != "Cancelled").first()
    if already:
        flash("You already have a booking for this trek.", "info")
        return redirect(url_for("user.dashboard"))

    booking = Booking(user_id=current_user.id, trek_id=trek.id, status="Booked")
    trek.available_slots -= 1

    db.session.add(booking)
    db.session.commit()
    flash(f"Booked {trek.name} successfully!", "success")
    return redirect(url_for("user.dashboard"))


@user_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
@trekker_only
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        abort(403)
    if booking.status != "Booked":
        flash("This booking cannot be cancelled.", "warning")
        return redirect(url_for("user.history"))

    booking.status = "Cancelled"
    # give back the slot
    trek = Trek.query.get(booking.trek_id)
    if trek and trek.available_slots < trek.total_slots:
        trek.available_slots += 1
    db.session.commit()
    flash("Booking cancelled.", "info")
    return redirect(url_for("user.history"))


@user_bp.route("/history")
@login_required
@trekker_only
def history():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.id.desc()).all()
    return render_template("user/history.html", bookings=bookings)


@user_bp.route("/profile", methods=["GET", "POST"])
@login_required
@trekker_only
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip()
        current_user.contact = request.form.get("contact", "").strip()
        current_user.email = request.form.get("email", current_user.email).strip()

        # optional password change
        new_pass = request.form.get("new_password", "")
        old_pass = request.form.get("old_password", "")
        if new_pass:
            if not check_password_hash(current_user.password, old_pass):
                flash("Old password incorrect.", "danger")
                return redirect(url_for("user.profile"))
            current_user.password = generate_password_hash(new_pass)

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("user.profile"))

    return render_template("user/profile.html")
