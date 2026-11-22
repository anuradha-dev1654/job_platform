import os

from flask import current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Company, Job
from app.utils.decorators import role_required
from app.utils.file_storage import save_company_logo
from . import bp


@bp.route("/dashboard", methods=["GET", "POST"])
@login_required
@role_required("company")
def dashboard():
    company = current_user.company
    if company is None:
        flash("Complete company registration before accessing the dashboard.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST" and request.form.get("action") == "update_profile":
        logo = request.files.get("logo")
        if logo and logo.filename:
            ext = os.path.splitext(logo.filename)[1].lower()
            head = logo.stream.read(8)
            logo.stream.seek(0)
            allowed = {".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".png": b"\x89PNG"}
            logo.seek(0, os.SEEK_END)
            size = logo.tell()
            logo.seek(0)
            if ext not in allowed or not head.startswith(allowed[ext]):
                flash("Upload a valid JPG or PNG company logo.", "error")
                return redirect(url_for("company.dashboard"))
            if size > 5 * 1024 * 1024:
                flash("Company logo must be 5 MB or smaller.", "error")
                return redirect(url_for("company.dashboard"))
            company.logo_path = save_company_logo(logo, company.id)
        company.website = request.form.get("website", "").strip() or None
        company.city = request.form.get("city", "").strip() or None
        company.address = request.form.get("address", "").strip() or None
        company.description = request.form.get("description", "").strip() or None
        company.industry = request.form.get("industry", "").strip() or None
        company.company_size = request.form.get("company_size", "").strip() or None
        founded_year = request.form.get("founded_year", "").strip()
        company.founded_year = int(founded_year) if founded_year.isdigit() else None
        rating = request.form.get("rating", "").strip()
        company.rating = float(rating) if rating else None
        benefits = [item.strip() for item in request.form.get("benefits", "").split(",") if item.strip()]
        company.benefits = benefits
        db.session.commit()
        flash("Company information updated.", "success")
        return redirect(url_for("company.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        if len(title) < 3:
            flash("Enter a valid job title.", "error")
        elif len(location) < 2:
            flash("Enter a valid job location.", "error")
        elif len(description) < 20:
            flash("Job description must be at least 20 characters.", "error")
        else:
            openings = request.form.get("openings", "1").strip()
            try:
                openings = int(openings)
            except ValueError:
                openings = 1
            skills = [item.strip() for item in request.form.get("key_skills", "").split(",") if item.strip()]
            db.session.add(Job(
                company_id=company.id,
                title=title,
                location=location,
                description=description,
                salary=request.form.get("salary", "").strip() or None,
                experience=request.form.get("experience", "").strip() or None,
                openings=max(openings, 1),
                role=request.form.get("role", "").strip() or title,
                industry=request.form.get("industry", "").strip() or company.industry,
                department=request.form.get("department", "").strip() or None,
                employment_type=request.form.get("employment_type", "").strip() or "Full Time",
                role_category=request.form.get("role_category", "").strip() or None,
                ug_qualification=request.form.get("ug_qualification", "").strip() or None,
                pg_qualification=request.form.get("pg_qualification", "").strip() or None,
                key_skills=skills,
            ))
            db.session.commit()
            flash("Job posted successfully.", "success")
            return redirect(url_for("company.dashboard"))

    jobs = db.session.execute(
        db.select(Job).where(Job.company_id == company.id).order_by(Job.created_at.desc())
    ).scalars().all()
    return render_template("company/dashboard.html", company=company, jobs=jobs)
