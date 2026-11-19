"""The whole backend: receives quote requests, saves them, and runs the admin page.

Run it locally with:  python app.py
Run it on Render with: gunicorn --preload app:app
"""
import hmac
import os
import re
import secrets
import threading
from datetime import date, datetime, timedelta, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

import email_sender
import excel_export

load_dotenv()

# ---------------------------------------------------------------------------
# Settings (all come from the .env file locally, or from Render's environment)
# ---------------------------------------------------------------------------

DEBUG = os.environ.get("DEBUG") == "1"
SECRET_KEY = os.environ.get("SECRET_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
FRONTEND_URL = (os.environ.get("FRONTEND_URL") or "https://portfolio.shakaaraahllc.com").rstrip("/")
ALLOWED_ORIGINS = [o.strip() for o in (os.environ.get("FRONTEND_ORIGINS") or FRONTEND_URL).split(",") if o.strip()]

if not SECRET_KEY or not ADMIN_PASSWORD:
    raise RuntimeError("SECRET_KEY and ADMIN_PASSWORD must be set. Copy .env.example to .env and fill them in.")
if len(ADMIN_PASSWORD) < 12:
    raise RuntimeError("ADMIN_PASSWORD must be at least 12 characters.")


def fix_database_url(url):
    """Hosts give a plain mysql:// address, but SQLAlchemy needs to be told which driver to use."""
    if url.startswith("mysql://"):
        url = "mysql+pymysql://" + url[len("mysql://"):]
    return url


app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=fix_database_url(os.environ.get("DATABASE_URL") or "sqlite:///quotes.db"),
    # MySQL servers close idle connections. This checks a connection is alive before using it.
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
    MAX_CONTENT_LENGTH=64 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=not DEBUG,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SEND_EMAILS_IN_BACKGROUND=True,
)
# Render sits in front of the app, so this is how we see the visitor's real address for rate limiting.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS, "methods": ["POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})
limiter = Limiter(key_func=get_remote_address, app=app, default_limits=["200 per hour"], storage_uri="memory://")
db = SQLAlchemy(app)

# Lagos has no daylight saving, so a fixed +1 hour offset is always right.
LAGOS = timezone(timedelta(hours=1))
MAX_EXPORT_ROWS = 10000
QUOTES_PER_PAGE = 20


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(12), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    source_page = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, index=True, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    client_email_sent = db.Column(db.Boolean, nullable=False, default=False)
    team_email_sent = db.Column(db.Boolean, nullable=False, default=False)


with app.app_context():
    db.create_all()


def to_lagos_time(stored_time):
    """Times are stored in UTC. This converts one to Lagos time."""
    return stored_time.replace(tzinfo=timezone.utc).astimezone(LAGOS)


def format_lagos_time(stored_time):
    local = to_lagos_time(stored_time)
    hour = local.hour % 12 or 12
    am_or_pm = "AM" if local.hour < 12 else "PM"
    return f"{local.day} {local:%b %Y}, {hour}:{local:%M} {am_or_pm}"


@app.template_filter("lagos_time")
def lagos_time_filter(stored_time):
    return format_lagos_time(stored_time)


def make_reference():
    letters_and_digits = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "SQ-" + "".join(secrets.choice(letters_and_digits) for _ in range(6))


# ---------------------------------------------------------------------------
# Checking what the visitor typed
# ---------------------------------------------------------------------------

CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WHATSAPP_PATTERN = re.compile(r"^\+?[0-9]{8,15}$")


def clean_text(value, keep_newlines=False):
    if not isinstance(value, str):
        return ""
    value = CONTROL_CHARACTERS.sub("", value.replace("\r\n", "\n"))
    if keep_newlines:
        return value.strip()
    return " ".join(value.split())


def check_quote(payload):
    """Returns (clean_values, errors). If errors is not empty, nothing should be saved."""
    payload = payload if isinstance(payload, dict) else {}
    values = {
        "name": clean_text(payload.get("name")),
        "email": clean_text(payload.get("email")).lower(),
        "whatsapp": re.sub(r"[\s\-().]", "", clean_text(payload.get("whatsapp"))),
        "service": clean_text(payload.get("service")),
        "message": clean_text(payload.get("message"), keep_newlines=True),
        "source": clean_text(payload.get("source"))[:100] or "/",
        "website": clean_text(payload.get("website"))[:200],
    }

    errors = {}
    if not 2 <= len(values["name"]) <= 100:
        errors["name"] = ["Enter your name so we know who to reply to."]
    if not EMAIL_PATTERN.match(values["email"]) or len(values["email"]) > 255:
        errors["email"] = ["Your email address doesn’t look right. Check for typos and try again."]
    if not WHATSAPP_PATTERN.match(values["whatsapp"]):
        errors["whatsapp"] = ["Enter your WhatsApp number with the country code, for example +234 703 543 6057."]
    if not 1 <= len(values["service"]) <= 100:
        errors["service"] = ["Choose the service you need."]
    if not 10 <= len(values["message"]) <= 2000:
        errors["message"] = ["Tell us a little about your project, at least 10 characters."]
    return values, errors


# ---------------------------------------------------------------------------
# The website form sends its quote request here
# ---------------------------------------------------------------------------

@app.get("/api/v1/health")
def health():
    db.session.execute(db.text("SELECT 1"))
    return jsonify(success=True, status="healthy")


@app.post("/api/v1/quotes")
@limiter.limit("5 per hour;20 per day")
def create_quote():
    values, errors = check_quote(request.get_json(silent=True))
    if errors:
        return jsonify(success=False, message="Please correct the errors below.", errors=errors), 422

    success_message = "Your quote request has been sent. Check your email for a confirmation."
    if values["website"]:
        # Real visitors never see this hidden field, so a filled one means a bot. We pretend it worked.
        app.logger.warning("Spam trap filled, request discarded")
        return jsonify(success=True, message=success_message), 201

    quote = Quote(
        reference=make_reference(),
        name=values["name"],
        email=values["email"],
        whatsapp=values["whatsapp"],
        service=values["service"],
        message=values["message"],
        source_page=values["source"],
    )
    db.session.add(quote)
    db.session.commit()
    app.logger.info("Quote %s saved", quote.reference)

    send_emails(quote.id)
    return jsonify(success=True, message=success_message, data={"reference": quote.reference}), 201


def send_emails(quote_id):
    """The quote is already saved, so emails go out in the background and the visitor does not wait for them."""
    if app.config["SEND_EMAILS_IN_BACKGROUND"]:
        threading.Thread(target=send_emails_now, args=(quote_id,), daemon=True).start()
    else:
        send_emails_now(quote_id)


def send_emails_now(quote_id):
    with app.app_context():
        quote = db.session.get(Quote, quote_id)
        quote.client_email_sent, quote.team_email_sent = email_sender.send_quote_emails({
            "name": quote.name,
            "email": quote.email,
            "whatsapp_number": quote.whatsapp,
            "service": quote.service,
            "message": quote.message,
            "reference": quote.reference,
            "source_page": quote.source_page,
            "received_at": format_lagos_time(quote.created_at),
        })
        db.session.commit()


# ---------------------------------------------------------------------------
# The admin page: sign in, see requests, download them as Excel
# ---------------------------------------------------------------------------

def admin_only(view):
    @wraps(view)
    def checked_view(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return checked_view


@app.get("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        typed_password = request.form.get("password", "")
        # compare_digest takes the same time however many letters match, so timing reveals nothing.
        if hmac.compare_digest(typed_password.encode(), ADMIN_PASSWORD.encode()):
            session.clear()
            session.permanent = True
            session["is_admin"] = True
            app.logger.info("Admin signed in")
            return redirect(url_for("dashboard"))
        app.logger.warning("Failed admin sign-in")
        return render_template("login.html", error="Incorrect password."), 401
    return render_template("login.html")


@app.post("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/admin")
@admin_only
def dashboard():
    page = max(request.args.get("page", 1, type=int), 1)
    today = datetime.now(LAGOS).date()
    return render_template(
        "dashboard.html",
        pagination=Quote.query.order_by(Quote.created_at.desc()).paginate(page=page, per_page=QUOTES_PER_PAGE, error_out=False),
        total=Quote.query.count(),
        default_from=(today - timedelta(days=30)).isoformat(),
        today=today.isoformat(),
        frontend_url=FRONTEND_URL,
    )


@app.get("/admin/export")
@admin_only
@limiter.limit("30 per hour")
def export_quotes():
    try:
        first_day = date.fromisoformat(request.args.get("from", ""))
        last_day = date.fromisoformat(request.args.get("to", ""))
    except ValueError:
        flash("Choose a start date and an end date.")
        return redirect(url_for("dashboard"))
    if last_day < first_day:
        flash("The end date comes before the start date.")
        return redirect(url_for("dashboard"))
    if (last_day - first_day).days > 366:
        flash("Choose a range of one year or less.")
        return redirect(url_for("dashboard"))

    # Each day runs from midnight to midnight in Lagos. The database stores UTC, so shift the range back one hour.
    start = datetime.combine(first_day, datetime.min.time()) - timedelta(hours=1)
    end = datetime.combine(last_day + timedelta(days=1), datetime.min.time()) - timedelta(hours=1)
    quotes = (Quote.query.filter(Quote.created_at >= start, Quote.created_at < end)
              .order_by(Quote.created_at).limit(MAX_EXPORT_ROWS + 1).all())
    if len(quotes) > MAX_EXPORT_ROWS:
        flash(f"That range has more than {MAX_EXPORT_ROWS:,} requests. Choose a shorter range.")
        return redirect(url_for("dashboard"))

    app.logger.info("Admin exported %s quotes, %s to %s", len(quotes), first_day, last_day)
    rows = [[q.reference, to_lagos_time(q.created_at).replace(tzinfo=None), q.name, q.whatsapp,
             q.email, q.service, q.message, q.source_page] for q in quotes]
    return send_file(
        excel_export.build_workbook(rows),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"shakaaraah-quotes_{first_day}_to_{last_day}.xlsx",
    )


# ---------------------------------------------------------------------------
# Safety nets
# ---------------------------------------------------------------------------

ERROR_MESSAGES = {
    400: "The request could not be understood. Please check your input.",
    404: "That page could not be found.",
    405: "This action is not allowed here.",
    413: "That request is larger than we accept.",
    429: "Too many requests. Please wait a moment before trying again.",
}


@app.errorhandler(HTTPException)
def handle_error(error):
    message = ERROR_MESSAGES.get(error.code, "An unexpected error occurred. Please try again later.")
    if request.path.startswith("/api/"):
        return jsonify(success=False, message=message), error.code
    return f"<h1>{error.code}</h1><p>{message}</p><p><a href='/admin'>Back to the dashboard</a></p>", error.code


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


if __name__ == "__main__":
    app.run(port=5000, debug=DEBUG)
