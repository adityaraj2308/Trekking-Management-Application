# staff.py
# routes for trek staff

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps

from database import db
from models import Trek, Booking, User

staff_bp = Blueprint("staff", __name__)


def staff_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "staff":
            abort(403)
        if current_user.status != "approved":
            flash("Waiting for admin approval.", "warning")
            return redirect(url_for("auth.home"))
        return f(*args, **kwargs)
    return wrapper


@staff_bp.route("/dashboard")
@login_required
@staff_only
def dashboard():
    # treks assigned to this staff
    treks = Trek.query.filter_by(staff_id=current_user.id).all()

    trek_data = []
    for t in treks:
        booked_count = Booking.query.filter_by(trek_id=t.id).filter(Booking.status != "Cancelled").count()
        trek_data.append({"trek": t, "booked_count": booked_count})

    return render_template("staff/dashboard.html", trek_data=trek_data)


@staff_bp.route("/trek/<int:trek_id>")
@login_required
@staff_only
def trek_detail(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user.id:
        abort(403)   # only assigned staff can access
    bookings = Booking.query.filter_by(trek_id=trek.id).all()
    return render_template("staff/trek_detail.html", trek=trek, bookings=bookings)


@staff_bp.route("/trek/<int:trek_id>/update", methods=["POST"])
@login_required
@staff_only
def trek_update(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if trek.staff_id != current_user.id:
        abort(403)

    # staff can only update slots and status
    try:
        new_slots = int(request.form.get("slots", trek.total_slots))
    except ValueError:
        new_slots = trek.total_slots

    already_booked = trek.total_slots - trek.available_slots
    if new_slots < already_booked:
        flash(f"Cannot reduce slots below already booked ({already_booked}).", "warning")
        return redirect(url_for("staff.trek_detail", trek_id=trek.id))

    trek.total_slots = new_slots
    trek.available_slots = new_slots - already_booked

    new_status = request.form.get("status")
    if new_status in ["Approved", "Open", "Closed", "Completed"]:
        trek.status = new_status
        # if trek is marked completed, mark all active bookings as completed too
        if new_status == "Completed":
            active = Booking.query.filter_by(trek_id=trek.id, status="Booked").all()
            for b in active:
                b.status = "Completed"

    db.session.commit()
    flash("Trek details updated.", "success")
    return redirect(url_for("staff.trek_detail", trek_id=trek.id))
