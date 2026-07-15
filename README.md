# Trekking Management Application (TrekMate)
A Flask-based Trekking Management System with role-based access for Admin, Trek Staff, and Trekkers, featuring trek management, bookings, staff approval, and SQLite database integration.

Simple trek management web app built for the project submission.

## Tech stack
- Flask (Python) - backend
- Jinja2 + HTML + CSS + Bootstrap 5 - frontend
- SQLite (via Flask-SQLAlchemy) - database
- Flask-Login - session management
- Chart.js (CDN) - dashboard charts

## Roles
1. **Admin** - pre-created (username: `admin`, password: `admin123`)
2. **Trek Staff** - registers and waits for admin approval
3. **User / Trekker** - registers and can browse + book treks directly

## How to run

1. Install dependencies
   ```
   pip install -r requirements.txt
   ```

2. Run the app
   ```
   python app.py
   ```
   The database (`trekking.db`) is created automatically on first run.
   The default admin is also seeded automatically.

3. Open in browser: http://127.0.0.1:5000

## Folder Structure

```
trekking_project/
├── app.py                # main flask app entry
├── database.py           # db object + init function
├── models.py             # SQLAlchemy models
├── requirements.txt
├── trekking.db           # (auto created)
├── controllers/
│   ├── auth.py           # login/register/logout
│   ├── admin.py          # admin routes
│   ├── staff.py          # trek staff routes
│   └── user.py           # trekker routes
├── static/
│   └── css/style.css
└── templates/
    ├── base.html
    ├── home.html
    ├── auth/
    ├── admin/
    ├── staff/
    └── user/
```

## Core features implemented
- Role based login for Admin, Staff, User
- Admin can add/edit/delete treks, approve/blacklist staff, blacklist users, assign staff to treks, search
- Staff can view assigned treks, update slots and status, view participant list
- Users can browse treks, filter by difficulty/location, book (only Open treks), cancel booking, view history, edit profile
- Prevents overbooking (available_slots check)
- Only assigned staff can manage a trek (permission check)
- Admin dashboard with charts (Popular Treks + Booking Status)

## Notes
- No JavaScript is used for any core requirement. JS is only used through Chart.js CDN and Bootstrap's built-in bundle (for navbar toggle and alert dismiss).
- Database tables are created programmatically via `db.create_all()` in `database.py`.
