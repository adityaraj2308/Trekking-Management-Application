# admin.py
# all admin side routes

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps

from database import db
from models import User, Trek, Booking

admin_bp = Blueprint("admin", __name__)


# small decorator to allow only admin
def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper


@admin_bp.route("/dashboard")
@login_required
@admin_only
def dashboard():
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="trekker").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()

    # for charts - popular treks (top 5 by bookings count)
    treks = Trek.query.all()
    chart_labels = []
    chart_values = []
    for t in treks:
        cnt = Booking.query.filter_by(trek_id=t.id).filter(Booking.status != "Cancelled").count()
        chart_labels.append(t.name)
        chart_values.append(cnt)

    # bookings by status pie
    status_labels = ["Booked", "Cancelled", "Completed"]
    status_values = [
        Booking.query.filter_by(status="Booked").count(),
        Booking.query.filter_by(status="Cancelled").count(),
        Booking.query.filter_by(status="Completed").count(),
    ]

    return render_template("admin/dashboard.html",
                           total_treks=total_treks,
                           total_users=total_users,
                           total_staff=total_staff,
                           total_bookings=total_bookings,
                           chart_labels=chart_labels,
                           chart_values=chart_values,
                           status_labels=status_labels,
                           status_values=status_values)


# ----- TREK MANAGEMENT -----

@admin_bp.route("/treks")
@login_required
@admin_only
def treks_list():
    q = request.args.get("q", "").strip()
    if q:
        # search by name or id
        if q.isdigit():
            treks = Trek.query.filter((Trek.name.ilike(f"%{q}%")) | (Trek.id == int(q))).all()
        else:
            treks = Trek.query.filter(Trek.name.ilike(f"%{q}%")).all()
    else:
        treks = Trek.query.order_by(Trek.id.desc()).all()

    staff_list = User.query.filter_by(role="staff", status="approved").all()
    return render_template("admin/treks.html", treks=treks, staff_list=staff_list, q=q)


@admin_bp.route("/treks/add", methods=["GET", "POST"])
@login_required
@admin_only
def trek_add():
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            location = request.form["location"].strip()
            difficulty = request.form["difficulty"]
            duration = int(request.form["duration"])
            price = float(request.form.get("price") or 0)
            slots = int(request.form["slots"])
            description = request.form.get("description", "")
            start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            flash("Please fill all fields correctly.", "warning")
            return redirect(url_for("admin.trek_add"))

        trek = Trek(name=name, location=location, difficulty=difficulty,
                    duration=duration, price=price,
                    total_slots=slots, available_slots=slots,
                    description=description,
                    start_date=start_date, end_date=end_date,
                    status="Pending")
        db.session.add(trek)
        db.session.commit()
        flash("Trek created successfully!", "success")
        return redirect(url_for("admin.treks_list"))
    return render_template("admin/trek_form.html", trek=None)


@admin_bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def trek_edit(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    if request.method == "POST":
        try:
            trek.name = request.form["name"].strip()
            trek.location = request.form["location"].strip()
            trek.difficulty = request.form["difficulty"]
            trek.duration = int(request.form["duration"])
            trek.price = float(request.form.get("price") or 0)
            new_slots = int(request.form["slots"])
            # adjust available slots properly
            already_booked = trek.total_slots - trek.available_slots
            trek.total_slots = new_slots
            trek.available_slots = max(0, new_slots - already_booked)
            trek.description = request.form.get("description", "")
            trek.start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
            trek.end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
            trek.status = request.form.get("status", trek.status)
        except (KeyError, ValueError):
            flash("Please fill all fields correctly.", "warning")
            return redirect(url_for("admin.trek_edit", trek_id=trek_id))

        db.session.commit()
        flash("Trek updated.", "success")
        return redirect(url_for("admin.treks_list"))
    return render_template("admin/trek_form.html", trek=trek)


@admin_bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@login_required
@admin_only
def trek_delete(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    # first delete bookings related to this trek
    Booking.query.filter_by(trek_id=trek.id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash("Trek removed.", "info")
    return redirect(url_for("admin.treks_list"))


@admin_bp.route("/treks/<int:trek_id>/assign", methods=["POST"])
@login_required
@admin_only
def trek_assign(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_id = request.form.get("staff_id")
    if not staff_id:
        flash("Please select a staff.", "warning")
        return redirect(url_for("admin.treks_list"))
    staff = User.query.filter_by(id=int(staff_id), role="staff", status="approved").first()
    if not staff:
        flash("Invalid staff selected.", "danger")
        return redirect(url_for("admin.treks_list"))
    trek.staff_id = staff.id
    # once staff assigned, admin can mark it approved
    if trek.status == "Pending":
        trek.status = "Approved"
    db.session.commit()
    flash(f"Assigned {staff.full_name or staff.username} to {trek.name}.", "success")
    return redirect(url_for("admin.treks_list"))


# ----- STAFF MANAGEMENT -----

@admin_bp.route("/staff")
@login_required
@admin_only
def staff_list():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="staff")
    if q:
        if q.isdigit():
            query = query.filter((User.username.ilike(f"%{q}%")) | (User.id == int(q)) | (User.full_name.ilike(f"%{q}%")))
        else:
            query = query.filter((User.username.ilike(f"%{q}%")) | (User.full_name.ilike(f"%{q}%")))
    staff = query.order_by(User.id.desc()).all()
    return render_template("admin/staff.html", staff=staff, q=q)


@admin_bp.route("/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
@admin_only
def staff_approve(staff_id):
    s = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    s.status = "approved"
    db.session.commit()
    flash(f"{s.username} approved.", "success")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:staff_id>/blacklist", methods=["POST"])
@login_required
@admin_only
def staff_blacklist(staff_id):
    s = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    s.status = "blacklisted"
    db.session.commit()
    flash(f"{s.username} blacklisted.", "warning")
    return redirect(url_for("admin.staff_list"))


@admin_bp.route("/staff/<int:staff_id>/unblacklist", methods=["POST"])
@login_required
@admin_only
def staff_unblacklist(staff_id):
    s = User.query.filter_by(id=staff_id, role="staff").first_or_404()
    s.status = "approved"
    db.session.commit()
    flash(f"{s.username} re-approved.", "success")
    return redirect(url_for("admin.staff_list"))


# ----- USER MANAGEMENT -----

@admin_bp.route("/users")
@login_required
@admin_only
def users_list():
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="trekker")
    if q:
        if q.isdigit():
            query = query.filter((User.username.ilike(f"%{q}%")) | (User.id == int(q)) | (User.full_name.ilike(f"%{q}%")))
        else:
            query = query.filter((User.username.ilike(f"%{q}%")) | (User.full_name.ilike(f"%{q}%")))
    users = query.order_by(User.id.desc()).all()
    return render_template("admin/users.html", users=users, q=q)


@admin_bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
@login_required
@admin_only
def user_blacklist(user_id):
    u = User.query.filter_by(id=user_id, role="trekker").first_or_404()
    u.status = "blacklisted"
    db.session.commit()
    flash(f"User {u.username} blacklisted.", "warning")
    return redirect(url_for("admin.users_list"))


@admin_bp.route("/users/<int:user_id>/activate", methods=["POST"])
@login_required
@admin_only
def user_activate(user_id):
    u = User.query.filter_by(id=user_id, role="trekker").first_or_404()
    u.status = "active"
    db.session.commit()
    flash(f"User {u.username} activated.", "success")
    return redirect(url_for("admin.users_list"))


# ----- BOOKINGS -----

@admin_bp.route("/bookings")
@login_required
@admin_only
def bookings_list():
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("admin/bookings.html", bookings=bookings)
