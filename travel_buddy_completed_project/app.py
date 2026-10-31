import os
from datetime import datetime, date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-development-secret")
db_url = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/travel_buddy")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), default="")
    bio = db.Column(db.String(500), default="")
    vehicle_preference = db.Column(db.String(20), default="Any")
    emergency_contact = db.Column(db.String(120), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    origin = db.Column(db.String(120), nullable=False, index=True)
    destination = db.Column(db.String(120), nullable=False, index=True)
    travel_date = db.Column(db.Date, nullable=False, index=True)
    departure_time = db.Column(db.Time, nullable=False)
    vehicle = db.Column(db.String(20), nullable=False)
    seats = db.Column(db.Integer, nullable=False, default=1)
    notes = db.Column(db.String(500), default="")
    status = db.Column(db.String(20), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.relationship("User", backref="trips")

class TravelRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(500), default="")
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trip = db.relationship("Trip", backref="requests")
    sender = db.relationship("User", foreign_keys=[sender_id])

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("travel_request.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.String(1000), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    request = db.relationship("TravelRequest", backref="messages")
    sender = db.relationship("User")

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])
    reviewee = db.relationship("User", foreign_keys=[reviewee_id])
    trip = db.relationship("Trip")

def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None

@app.context_processor
def inject_user():
    return {"current_user": current_user(), "today": date.today()}

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    upcoming = Trip.query.filter(Trip.status == "open", Trip.travel_date >= date.today()).order_by(Trip.travel_date).limit(6).all()
    return render_template("index.html", trips=upcoming)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Enter your name/email and a password of at least 8 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Welcome to Travel Buddy!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    my_trips = Trip.query.filter_by(owner_id=user.id).order_by(Trip.travel_date.desc()).all()
    incoming = TravelRequest.query.join(Trip).filter(Trip.owner_id == user.id).order_by(TravelRequest.created_at.desc()).all()
    outgoing = TravelRequest.query.filter_by(sender_id=user.id).order_by(TravelRequest.created_at.desc()).all()
    return render_template("dashboard.html", my_trips=my_trips, incoming=incoming, outgoing=outgoing)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        user.name = request.form.get("name", "").strip()[:80]
        user.city = request.form.get("city", "").strip()[:100]
        user.bio = request.form.get("bio", "").strip()[:500]
        user.vehicle_preference = request.form.get("vehicle_preference", "Any")
        user.emergency_contact = request.form.get("emergency_contact", "").strip()[:120]
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)

@app.route("/trips/new", methods=["GET", "POST"])
@login_required
def new_trip():
    if request.method == "POST":
        try:
            travel_date = date.fromisoformat(request.form["travel_date"])
            departure_time = datetime.strptime(request.form["departure_time"], "%H:%M").time()
            seats = int(request.form.get("seats", 1))
            origin = request.form.get("origin", "").strip()
            destination = request.form.get("destination", "").strip()
            vehicle = request.form.get("vehicle", "")
            if travel_date < date.today() or not origin or not destination or origin.casefold() == destination.casefold():
                raise ValueError("Check the route and choose today or a future date.")
            if seats < 1 or seats > 15 or vehicle not in {"Bike", "Car", "Van"}:
                raise ValueError("Choose a valid vehicle and seat count.")
            trip = Trip(owner_id=current_user().id, origin=origin, destination=destination,
                        travel_date=travel_date, departure_time=departure_time,
                        vehicle=vehicle, seats=seats, notes=request.form.get("notes", "").strip()[:500])
            db.session.add(trip)
            db.session.commit()
            flash("Trip published successfully.", "success")
            return redirect(url_for("trip_detail", trip_id=trip.id))
        except (ValueError, KeyError):
            flash("Please check the trip details. Dates must be today or later; seats must be 1–15.", "danger")
    return render_template("trip_form.html")

@app.route("/trips")
def search_trips():
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    vehicle = request.args.get("vehicle", "").strip()
    date_text = request.args.get("travel_date", "")
    flexible = request.args.get("flexible") == "1"
    query = Trip.query.filter(Trip.status == "open", Trip.travel_date >= date.today())
    if origin:
        query = query.filter(Trip.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Trip.destination.ilike(f"%{destination}%"))
    if vehicle in {"Bike", "Car", "Van"}:
        query = query.filter(Trip.vehicle == vehicle)
    if date_text:
        try:
            wanted = date.fromisoformat(date_text)
            if flexible:
                query = query.filter(Trip.travel_date.between(wanted - timedelta(days=1), wanted + timedelta(days=1)))
            else:
                query = query.filter(Trip.travel_date == wanted)
        except ValueError:
            flash("Invalid date filter.", "warning")
    trips = query.order_by(Trip.travel_date, Trip.departure_time).all()
    # Rank route/date relevance. This is a heuristic, not a distance/GPS calculation.
    def score(t):
        s = 0
        if origin and t.origin.casefold() == origin.casefold(): s += 4
        elif origin and origin.casefold() in t.origin.casefold(): s += 2
        if destination and t.destination.casefold() == destination.casefold(): s += 4
        elif destination and destination.casefold() in t.destination.casefold(): s += 2
        if date_text:
            try:
                delta = abs((t.travel_date - date.fromisoformat(date_text)).days)
                s += max(0, 3 - delta)
            except ValueError: pass
        return s
    trips.sort(key=score, reverse=True)
    return render_template("trips.html", trips=trips, origin=origin, destination=destination,
                           vehicle=vehicle, travel_date=date_text, flexible=flexible)

@app.route("/trips/<int:trip_id>")
def trip_detail(trip_id):
    trip = db.get_or_404(Trip, trip_id)
    return render_template("trip_detail.html", trip=trip)

@app.route("/trips/<int:trip_id>/edit", methods=["GET", "POST"])
@login_required
def edit_trip(trip_id):
    trip = db.get_or_404(Trip, trip_id)
    if trip.owner_id != current_user().id: abort(403)
    if request.method == "POST":
        try:
            travel_date = date.fromisoformat(request.form["travel_date"])
            departure_time = datetime.strptime(request.form["departure_time"], "%H:%M").time()
            seats = int(request.form.get("seats", 1))
            origin, destination = request.form.get("origin", "").strip(), request.form.get("destination", "").strip()
            vehicle = request.form.get("vehicle", "")
            if travel_date < date.today() or not origin or not destination or origin.casefold() == destination.casefold() or not 1 <= seats <= 15 or vehicle not in {"Bike", "Car", "Van"}:
                raise ValueError()
            trip.origin, trip.destination, trip.travel_date, trip.departure_time = origin, destination, travel_date, departure_time
            trip.vehicle, trip.seats = vehicle, seats
            trip.notes = request.form.get("notes", "").strip()[:500]
            db.session.commit()
            flash("Trip updated.", "success")
            return redirect(url_for("trip_detail", trip_id=trip.id))
        except (ValueError, KeyError):
            flash("Please check all trip fields.", "danger")
    return render_template("trip_form.html", trip=trip)

@app.route("/trips/<int:trip_id>/cancel", methods=["POST"])
@login_required
def cancel_trip(trip_id):
    trip = db.get_or_404(Trip, trip_id)
    if trip.owner_id != current_user().id: abort(403)
    trip.status = "cancelled"
    db.session.commit()
    flash("Trip cancelled.", "info")
    return redirect(url_for("dashboard"))

@app.route("/trips/<int:trip_id>/request", methods=["POST"])
@login_required
def request_to_join(trip_id):
    trip = db.get_or_404(Trip, trip_id)
    user = current_user()
    if trip.owner_id == user.id:
        flash("You cannot request to join your own trip.", "warning")
    elif trip.status != "open" or trip.travel_date < date.today():
        flash("This trip is no longer available.", "warning")
    elif TravelRequest.query.filter_by(trip_id=trip.id, sender_id=user.id).first():
        flash("You have already sent a request for this trip.", "warning")
    else:
        req = TravelRequest(trip_id=trip.id, sender_id=user.id, message=request.form.get("message", "").strip()[:500])
        db.session.add(req)
        db.session.commit()
        flash("Travel request sent to the trip owner.", "success")
    return redirect(url_for("trip_detail", trip_id=trip.id))

@app.route("/requests/<int:request_id>/<action>", methods=["POST"])
@login_required
def handle_request(request_id, action):
    req = db.get_or_404(TravelRequest, request_id)
    if req.trip.owner_id != current_user().id: abort(403)
    if action not in {"accept", "decline"}: abort(404)
    if req.status == "pending":
        req.status = "accepted" if action == "accept" else "declined"
        db.session.commit()
        flash(f"Request {req.status}.", "success")
    return redirect(url_for("dashboard"))

@app.route("/requests/<int:request_id>/chat", methods=["GET", "POST"])
@login_required
def chat(request_id):
    req = db.get_or_404(TravelRequest, request_id)
    user = current_user()
    if user.id not in {req.sender_id, req.trip.owner_id} or req.status != "accepted":
        abort(403)
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            db.session.add(Message(request_id=req.id, sender_id=user.id, body=body[:1000]))
            db.session.commit()
        return redirect(url_for("chat", request_id=req.id))
    messages = Message.query.filter_by(request_id=req.id).order_by(Message.created_at).all()
    return render_template("chat.html", req=req, messages=messages)

@app.route("/trips/<int:trip_id>/review", methods=["POST"])
@login_required
def review(trip_id):
    trip = db.get_or_404(Trip, trip_id)
    user = current_user()
    target_id = request.form.get("reviewee_id", type=int)
    rating = request.form.get("rating", type=int)
    if trip.travel_date > date.today() or user.id == trip.owner_id or target_id != trip.owner_id or rating not in range(1, 6):
        flash("Review cannot be submitted for this trip.", "danger")
    elif Review.query.filter_by(trip_id=trip.id, reviewer_id=user.id).first():
        flash("You have already reviewed this trip.", "warning")
    else:
        db.session.add(Review(trip_id=trip.id, reviewer_id=user.id, reviewee_id=target_id,
                              rating=rating, comment=request.form.get("comment", "").strip()[:500]))
        db.session.commit()
        flash("Review submitted.", "success")
    return redirect(url_for("trip_detail", trip_id=trip.id))

@app.route("/safety")
def safety():
    return render_template("safety.html")

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page or trip could not be found."), 404

@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    db.create_all()
    print("Travel Buddy tables created.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
