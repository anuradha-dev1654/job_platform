import hashlib, hmac, os, re, secrets, shutil, time
from urllib.parse import urlparse

from flask import render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from flask_mail import Message

from app.extensions import db, mail
from app.models import User, Company
from app.utils.file_storage import validate_upload, save_company_doc, save_company_logo
from . import bp
from .forms import RegisterForm, LoginForm

HOME = {"candidate": "candidate.dashboard", "company": "company.dashboard", "admin": "admin.dashboard"}


def _home(user):
    return redirect(url_for(HOME[user.role]))


def _safe_next(target):
    return bool(target) and target.startswith("/") and not target.startswith("//") and "\\" not in target


# ---------------- Candidate register / login / logout ----------------
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _home(current_user)
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data.strip(), email=form.email.data.strip().lower(), role="candidate")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _home(current_user)
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = db.session.scalar(db.select(User).filter_by(email=email))
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            nxt = request.args.get("next")
            return redirect(nxt) if _safe_next(nxt) else _home(user)
        flash("Invalid email or password.", "error")
    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))


# ---------------- Company registration ----------------
FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com",
                "rediffmail.com", "proton.me", "protonmail.com"}
DESIGNATIONS = ["Founder / Owner", "Director", "HR Manager", "Recruiter", "Other authorised representative"]
BUSINESS_TYPES = ["Private Limited", "Public Limited", "LLP", "Partnership",
                  "Proprietorship", "Startup", "NGO / Trust", "Other"]
ID_PATTERNS = {
    "PAN": r"^[A-Z]{5}[0-9]{4}[A-Z]$",
    "GST": r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$",
    "CIN": r"^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$",
}
DOC_FIELDS = ["rep_id", "auth_letter", "incorp_cert", "gst_pan", "owner_id"]
OTP_TTL, OTP_COOLDOWN, OTP_MAX_TRIES = 600, 30, 5


def _is_company_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)) and \
        email.rsplit("@", 1)[1].lower() not in FREE_DOMAINS


def _hash_otp(otp):
    return hashlib.sha256((current_app.config["SECRET_KEY"] + otp).encode()).hexdigest()


@bp.post("/company/send-otp")
def company_send_otp():
    email = (request.get_json(silent=True) or {}).get("email", "").strip().lower()
    if not _is_company_email(email):
        return jsonify(ok=False, error="Use your official company email, not Gmail, Yahoo, etc."), 400
    if db.session.scalar(db.select(User).filter_by(email=email)):
        return jsonify(ok=False, error="This email is already registered."), 400
    if time.time() - session.get("otp_sent_at", 0) < OTP_COOLDOWN:
        return jsonify(ok=False, error="Please wait a few seconds before requesting another OTP."), 429

    otp = f"{secrets.randbelow(10**6):06d}"
    session.update(otp_email=email, otp_hash=_hash_otp(otp), otp_exp=time.time() + OTP_TTL,
                   otp_sent_at=time.time(), otp_tries=0)
    session.pop("otp_verified_email", None)

    if current_app.config.get("MAIL_USERNAME"):
        try:
            mail.send(Message("Your CareerBridge verification code", recipients=[email],
                              body=f"Your OTP is {otp}. It expires in 10 minutes."))
        except Exception:
            current_app.logger.exception("OTP email failed")
            return jsonify(ok=False, error="Could not send the email. Try again later."), 500
    else:
        current_app.logger.warning("DEV MODE: OTP for %s is %s", email, otp)  # shown in terminal
    return jsonify(ok=True)


@bp.post("/company/verify-otp")
def company_verify_otp():
    data = request.get_json(silent=True) or {}
    email, otp = data.get("email", "").strip().lower(), str(data.get("otp", "")).strip()
    if session.get("otp_email") != email or time.time() > session.get("otp_exp", 0):
        return jsonify(ok=False, error="OTP expired. Request a new one."), 400
    if session.get("otp_tries", 0) >= OTP_MAX_TRIES:
        return jsonify(ok=False, error="Too many attempts. Request a new OTP."), 429
    session["otp_tries"] = session.get("otp_tries", 0) + 1
    if not hmac.compare_digest(session.get("otp_hash", ""), _hash_otp(otp)):
        return jsonify(ok=False, error="Incorrect OTP."), 400
    session["otp_verified_email"] = email
    session.pop("otp_hash", None)
    return jsonify(ok=True)


@bp.route("/register/company", methods=["GET", "POST"])
def register_company():
    if current_user.is_authenticated:
        return _home(current_user)

    errors, v = {}, {}
    if request.method == "POST":
        v = request.form.to_dict()
        email = v.get("rep_email", "").strip().lower()
        cid_type, cid = v.get("corporate_id_type", ""), v.get("corporate_id", "").strip().upper()
        site = urlparse(v.get("website", "").strip())
        pw = request.form.get("password", "")

        if not v.get("rep_name", "").strip():
            errors["rep_name"] = "Enter your full name."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors["rep_email"] = "Enter a valid company email."
        elif db.session.scalar(db.select(User).filter_by(email=email)):
            errors["rep_email"] = "This email is already registered."

        if not v.get("company_name", "").strip():
            errors["company_name"] = "Enter the company name."
        if cid and (cid_type not in ID_PATTERNS or not re.match(ID_PATTERNS[cid_type], cid)):
            errors["corporate_id"] = f"Enter a valid {cid_type or 'corporate'} number."
        elif cid and db.session.scalar(db.select(Company).filter_by(corporate_id=cid)):
            errors["corporate_id"] = "A company with this ID is already registered."
        if v.get("website", "").strip() and (site.scheme not in ("http", "https") or not site.netloc):
            errors["website"] = "Enter the full website address, e.g. https://example.com"
        if v.get("phone", "").strip() and not re.match(r"^[6-9]\d{9}$", v.get("phone", "").strip()):
            errors["phone"] = "Enter a valid 10-digit mobile number."

        logo = request.files.get("company_logo")
        logo_ok = True
        if logo and logo.filename:
            ext = os.path.splitext(logo.filename)[1].lower()
            head = logo.stream.read(8)
            logo.stream.seek(0)
            allowed = {".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".png": b"\x89PNG"}
            logo.seek(0, os.SEEK_END)
            size = logo.tell()
            logo.seek(0)
            if ext not in allowed or not head.startswith(allowed[ext]):
                logo_ok = False
                errors["company_logo"] = "Upload a valid JPG or PNG logo."
            elif size > 5 * 1024 * 1024:
                logo_ok = False
                errors["company_logo"] = "Logo must be 5 MB or smaller."

        files = {}
        for key in DOC_FIELDS:
            uploaded = request.files.get(key)
            if uploaded and uploaded.filename:
                ok, msg = validate_upload(uploaded)
                if ok:
                    files[key] = uploaded
                else:
                    errors[key] = msg

        if len(pw) < 8:
            errors["password"] = "Password must be at least 8 characters."
        elif pw != request.form.get("confirm_password", ""):
            errors["confirm_password"] = "Passwords do not match."
        for box in ("confirm_info", "agree_terms"):
            if not v.get(box):
                errors[box] = "Please tick this box to continue."

        if not errors:
            user = User(name=v["rep_name"].strip(), email=email, role="company")
            user.set_password(pw)
            db.session.add(user)
            db.session.flush()
            company = Company(
                user_id=user.id,
                name=v["company_name"].strip(),
                website=v.get("website", "").strip() or None,
                rep_designation=v.get("designation") or None,
                corporate_id_type=cid_type or None,
                corporate_id=cid or None,
                business_type=v.get("business_type") or None,
                address=v.get("address", "").strip() or None,
                city=v.get("city", "").strip() or None,
                phone=v.get("phone", "").strip() or None,
                is_approved=True,
                industry=v.get("industry", "").strip() or None,
                company_size=v.get("company_size", "").strip() or None,
                founded_year=int(v["founded_year"]) if v.get("founded_year", "").strip().isdigit() else None,
                description=v.get("description", "").strip() or None,
                rating=float(v["rating"]) if v.get("rating", "").strip() else None,
                benefits=[item.strip() for item in v.get("benefits", "").split(",") if item.strip()],
            )
            db.session.add(company)
            db.session.flush()
            company_id = company.id
            try:
                company.documents = {k: save_company_doc(f, company_id) for k, f in files.items()}
                if logo and logo_ok:
                    company.logo_path = save_company_logo(logo, company_id)
                db.session.commit()
            except Exception:
                db.session.rollback()
                shutil.rmtree(os.path.join(current_app.config["UPLOAD_FOLDER"], "company_docs",
                                           str(company_id)), ignore_errors=True)
                current_app.logger.exception("Company registration failed")
                flash("Something went wrong while saving. Please try again.", "error")
            else:
                for k in ("otp_email", "otp_verified_email", "otp_exp", "otp_sent_at", "otp_tries"):
                    session.pop(k, None)
                flash("Company registered successfully. You can now sign in and post jobs.", "success")
                return redirect(url_for("auth.login"))

    return render_template("company/register_company.html", errors=errors, v=v,
                           designations=DESIGNATIONS, business_types=BUSINESS_TYPES,
                           id_types=list(ID_PATTERNS), verified_email=session.get("otp_verified_email", ""))