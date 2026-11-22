import os

from flask import current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import Application, CandidateProfile, Company, Job, SavedJob
from sqlalchemy import or_
from app.utils.decorators import role_required
from . import bp

CATEGORIES = [
    "Remote", "MNC", "Internship", "Engineering", "Data Science",
    "HR", "Marketing", "Analytics", "Sales", "Banking", "Startup",
]


@bp.route("/")
def index():
    total_jobs = db.session.scalar(db.select(db.func.count(Job.id))) or 0

    # approved companies, most open jobs first
    job_count = db.func.count(Job.id)
    rows = db.session.execute(
        db.select(Company, job_count)
        .outerjoin(Job, Job.company_id == Company.id)
        .where(Company.is_approved.is_(True))
        .group_by(Company.id)
        .order_by(job_count.desc())
        .limit(10)
    ).all()
    companies = [{"id": c.id, "name": c.name, "jobs": n, "trust": c.trust_score,
                  "logo_path": c.logo_path} for c, n in rows]

    return render_template("home.html", total_jobs=total_jobs,
                           categories=CATEGORIES, companies=companies)


@bp.route("/search")
def search():
    q = request.args.get("q", "").strip()
    loc = request.args.get("loc", "").strip()

    stmt = db.select(Job, Company).join(Company, Job.company_id == Company.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Job.title.ilike(like), Job.description.ilike(like),
                              Company.name.ilike(like)))
    if loc:
        stmt = stmt.where(or_(Job.location.ilike(f"%{loc}%"),
                              Company.city.ilike(f"%{loc}%")))

    stmt = stmt.order_by(Job.created_at.desc())
    results = db.session.execute(stmt).all()
    jobs = [{"job": job, "company": company} for job, company in results]

    if q and not jobs:
        exact_company = db.session.scalar(
            db.select(Company).where(db.func.lower(Company.name) == q.lower())
        )
        if exact_company:
            return redirect(url_for("jobs.company_detail", company_id=exact_company.id))

    return render_template(
        "jobs/search.html",
        jobs=jobs,
        q=q,
        loc=loc,
        experience=request.args.get("exp", "").strip(),
    )


@bp.route("/job/<int:job_id>")
def job_detail(job_id):
    row = db.session.execute(
        db.select(Job, Company).join(Company, Job.company_id == Company.id).where(Job.id == job_id)
    ).first()
    if not row:
        return render_template("errors/404.html"), 404

    job, company = row
    title_words = [word for word in job.title.split() if len(word) >= 3]
    similar_stmt = db.select(Job, Company).join(Company, Job.company_id == Company.id).where(
        Job.id != job.id
    )
    filters = [Job.location.ilike(f"%{job.location}%")] if job.location else []
    for word in title_words[:3]:
        filters.append(Job.title.ilike(f"%{word}%"))
    if filters:
        similar_stmt = similar_stmt.where(or_(*filters))
    similar_rows = db.session.execute(similar_stmt.limit(8)).all()
    similar_jobs = [{"job": similar_job, "company": similar_company}
                    for similar_job, similar_company in similar_rows]

    application = None
    saved = False
    candidate_profile = None
    if current_user.is_authenticated and getattr(current_user, "role", None) == "candidate":
        application = db.session.scalar(
            db.select(Application).where(Application.candidate_id == current_user.id,
                                         Application.job_id == job.id)
        )
        saved = db.session.scalar(
            db.select(SavedJob).where(SavedJob.candidate_id == current_user.id,
                                      SavedJob.job_id == job.id)
        ) is not None
        candidate_profile = current_user.candidate_profile

    return render_template(
        "jobs/detail.html",
        job=job,
        company=company,
        similar_jobs=similar_jobs,
        application=application,
        saved=saved,
        candidate_profile=candidate_profile,
    )


@bp.route("/company/<int:company_id>")
def company_detail(company_id):
    company = db.session.get(Company, company_id)
    if not company:
        return render_template("errors/404.html"), 404
    company_jobs = db.session.execute(
        db.select(Job).where(Job.company_id == company.id).order_by(Job.created_at.desc())
    ).scalars().all()
    return render_template("jobs/company_detail.html", company=company, company_jobs=company_jobs)


@bp.route("/company/<int:company_id>/logo")
def company_logo(company_id):
    company = db.session.get(Company, company_id)
    if not company or not company.logo_path:
        return render_template("errors/404.html"), 404
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], company.logo_path)


@bp.route("/job/<int:job_id>/apply", methods=["POST"])
@login_required
@role_required("candidate")
def apply_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return render_template("errors/404.html"), 404

    existing = db.session.scalar(
        db.select(Application).where(Application.candidate_id == current_user.id,
                                      Application.job_id == job.id)
    )
    if existing:
        flash("You have already applied for this job.", "success")
        return redirect(url_for("jobs.job_detail", job_id=job.id))

    candidate_profile = current_user.candidate_profile
    resume_path = candidate_profile.resume_path if candidate_profile else None
    resume_file = request.files.get("resume")
    if resume_file and resume_file.filename:
        ext = os.path.splitext(resume_file.filename)[1].lower()
        head = resume_file.stream.read(8)
        resume_file.stream.seek(0)
        if ext not in (".pdf", ".doc", ".docx") or (ext == ".pdf" and not head.startswith(b"%PDF")):
            flash("Upload a valid PDF, DOC or DOCX resume.", "error")
            return redirect(url_for("jobs.job_detail", job_id=job.id))
        resume_file.seek(0, os.SEEK_END)
        if resume_file.tell() > 5 * 1024 * 1024:
            flash("Resume must be 5 MB or smaller.", "error")
            return redirect(url_for("jobs.job_detail", job_id=job.id))
        resume_file.seek(0)
        folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "applications",
                              str(current_user.id), str(job.id))
        os.makedirs(folder, exist_ok=True)
        name = f"{secure_filename(resume_file.filename)}"
        resume_file.save(os.path.join(folder, name))
        resume_path = f"applications/{current_user.id}/{job.id}/{name}"

    application = Application(
        candidate_id=current_user.id,
        job_id=job.id,
        cover_letter=request.form.get("cover_letter", "").strip() or None,
        phone=request.form.get("phone", "").strip() or None,
        experience=request.form.get("experience", "").strip() or None,
        resume_path=resume_path,
        status="applied",
    )
    db.session.add(application)
    db.session.commit()
    flash("Application submitted successfully.", "success")
    return redirect(url_for("jobs.job_detail", job_id=job.id))


@bp.route("/job/<int:job_id>/save", methods=["POST"])
@login_required
@role_required("candidate")
def save_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return render_template("errors/404.html"), 404
    saved = db.session.scalar(
        db.select(SavedJob).where(SavedJob.candidate_id == current_user.id,
                                  SavedJob.job_id == job.id)
    )
    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash("Job removed from saved jobs.", "success")
    else:
        db.session.add(SavedJob(candidate_id=current_user.id, job_id=job.id))
        db.session.commit()
        flash("Job saved successfully.", "success")
    return redirect(url_for("jobs.job_detail", job_id=job.id))


@bp.route("/application/resume/<int:application_id>")
@login_required
def application_resume(application_id):
    application = db.session.get(Application, application_id)
    if not application:
        return render_template("errors/404.html"), 404
    allowed = (application.candidate_id == current_user.id or
               getattr(current_user, "role", None) == "admin")
    if not allowed:
        return render_template("errors/404.html"), 404
    if not application.resume_path:
        return render_template("errors/404.html"), 404
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], application.resume_path)