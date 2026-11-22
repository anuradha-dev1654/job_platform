import os
from datetime import date

import pymupdf
from flask import current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.models import CandidateProfile, Company, Job, Resume, User
from app.utils.decorators import role_required
from app.utils.file_storage import save_candidate_file
from . import bp


SECTION_KEYS = (
    "preferences",
    "education",
    "key_skills",
    "languages",
    "internships",
    "projects",
    "profile_summary",
    "certifications",
    "awards",
    "clubs",
    "competitive_exams",
    "employment",
    "academic_achievements",
)


def _get_profile():
    profile = current_user.candidate_profile
    if profile is None:
        profile = CandidateProfile(user_id=current_user.id, sections={})
        db.session.add(profile)
        db.session.flush()
    return profile


def _profile_completion(profile):
    fields = (
        (profile and profile.headline),
        (profile and profile.location),
        (profile and profile.phone),
        (profile and profile.gender),
        (profile and profile.birthday),
        (profile and profile.photo_path),
        (profile and profile.resume_path),
    )

    completed = sum(5 for value in fields if value)
    sections = profile.sections if profile and isinstance(profile.sections, dict) else {}
    for key in SECTION_KEYS:
        value = sections.get(key)
        if isinstance(value, dict):
            populated = any(bool(item) for item in value.values())
        elif isinstance(value, (list, tuple, set)):
            populated = bool(value)
        else:
            populated = bool(value)
        if populated:
            completed += 5
    return min(completed, 100)


@bp.route("/dashboard")
@login_required
@role_required("candidate")
def dashboard():
    candidate_profile = _get_profile()
    db.session.commit()
    preferred_location = candidate_profile.location if candidate_profile else None

    job_stmt = db.select(Job, Company).join(Company, Job.company_id == Company.id)
    if preferred_location:
        job_stmt = job_stmt.where(or_(Job.location.ilike(f"%{preferred_location}%"),
                                      Company.city.ilike(f"%{preferred_location}%")))
    job_rows = db.session.execute(job_stmt.limit(6)).all()
    recommended_jobs = [
        {
            "id": job.id,
            "company_id": company.id,
            "title": job.title,
            "company": company.name,
            "location": job.location or company.city or "Location not specified",
            "mode": "On-site" if job.location else "Flexible",
            "experience": "All experience levels",
            "salary": "Not disclosed",
            "match": 80,
            "initial": company.name[:1].upper(),
            "logo_path": company.logo_path,
            "tone": "blue",
        }
        for job, company in job_rows
    ]

    company_rows = db.session.execute(
        db.select(Company).where(Company.is_approved.is_(True)).limit(6)
    ).scalars().all()
    companies = [
        {
            "id": company.id,
            "name": company.name,
            "logo_path": company.logo_path,
            "rating": "New",
            "reviews": "0",
            "initial": company.name[:1].upper(),
            "tone": "blue",
        }
        for company in company_rows
    ]
    return render_template(
        "candidate/dashboard.html",
        candidate=current_user,
        profile_completion=_profile_completion(candidate_profile),
        recommended_jobs=recommended_jobs,
        companies=companies,
    )


@bp.route("/profile")
@login_required
@role_required("candidate")
def profile():
    candidate_profile = _get_profile()
    db.session.commit()
    sections = candidate_profile.sections or {}
    skill_value = sections.get("key_skills", {})
    if isinstance(skill_value, dict):
        skills = skill_value.get("skills", [])
    elif isinstance(skill_value, str):
        skills = [skill.strip() for skill in skill_value.split(",") if skill.strip()]
    else:
        skills = skill_value or []

    return render_template(
        "candidate/profile.html",
        candidate=current_user,
        candidate_profile=candidate_profile,
        sections=sections,
        profile_completion=_profile_completion(candidate_profile),
        skills=skills,
    )


@bp.route("/profile/save", methods=["POST"])
@login_required
@role_required("candidate")
def save_profile_section():
    candidate_profile = _get_profile()
    section = request.form.get("section", "").strip()

    if section == "basic":
        current_user.name = request.form.get("name", "").strip() or current_user.name
        email = request.form.get("email", "").strip().lower()
        if email:
            existing = db.session.scalar(db.select(User).filter_by(email=email))
            if existing and existing.id != current_user.id:
                flash("This email is already registered.", "error")
                return redirect(url_for("candidate.profile"))
            current_user.email = email
        candidate_profile.headline = request.form.get("headline", "").strip() or None
        candidate_profile.location = request.form.get("location", "").strip() or None
        candidate_profile.phone = request.form.get("phone", "").strip() or None
        candidate_profile.gender = request.form.get("gender", "").strip() or None
        birthday = request.form.get("birthday", "").strip()
        candidate_profile.birthday = date.fromisoformat(birthday) if birthday else None
    elif section in SECTION_KEYS:
        values = {
            key: value.strip()
            for key, value in request.form.items()
            if key not in ("section", "csrf_token") and value.strip()
        }
        if section == "key_skills":
            values = {
                "skills": [
                    skill.strip()
                    for skill in request.form.get("skills", "").split(",")
                    if skill.strip()
                ]
            }
        elif section == "languages":
            values = {
                "languages": [
                    language.strip()
                    for language in request.form.get("languages", "").split(",")
                    if language.strip()
                ]
            }
        updated = dict(candidate_profile.sections or {})
        updated[section] = values
        candidate_profile.sections = updated
    else:
        flash("Invalid profile section.", "error")
        return redirect(url_for("candidate.profile"))

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("candidate.profile"))


@bp.route("/profile/photo", methods=["POST"])
@login_required
@role_required("candidate")
def upload_photo():
    photo = request.files.get("photo")
    if not photo or not photo.filename:
        flash("Choose a photo to upload.", "error")
        return redirect(url_for("candidate.profile"))

    ext = os.path.splitext(photo.filename)[1].lower()
    allowed = {".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff", ".png": b"\x89PNG"}
    head = photo.stream.read(8)
    photo.stream.seek(0)
    if ext not in allowed or not head.startswith(allowed[ext]):
        flash("Upload a valid JPG or PNG photo.", "error")
        return redirect(url_for("candidate.profile"))
    photo.seek(0, os.SEEK_END)
    size = photo.tell()
    photo.seek(0)
    if size > 5 * 1024 * 1024:
        flash("Photo must be 5 MB or smaller.", "error")
        return redirect(url_for("candidate.profile"))

    candidate_profile = _get_profile()
    candidate_profile.photo_path = save_candidate_file(photo, current_user.id, "photo")
    db.session.commit()
    flash("Profile photo uploaded.", "success")
    return redirect(url_for("candidate.profile"))


@bp.route("/profile/resume", methods=["POST"])
@login_required
@role_required("candidate")
def upload_resume():
    resume_file = request.files.get("resume")
    if not resume_file or not resume_file.filename:
        flash("Choose a resume to upload.", "error")
        return redirect(url_for("candidate.profile"))

    ext = os.path.splitext(resume_file.filename)[1].lower()
    head = resume_file.stream.read(8)
    resume_file.stream.seek(0)
    if ext not in (".pdf", ".doc", ".docx"):
        flash("Upload a PDF, DOC or DOCX resume.", "error")
        return redirect(url_for("candidate.profile"))
    if ext == ".pdf" and not head.startswith(b"%PDF"):
        flash("This PDF file is invalid.", "error")
        return redirect(url_for("candidate.profile"))
    if ext == ".doc" and not head.startswith(b"\xd0\xcf\x11\xe0"):
        flash("This DOC file is invalid.", "error")
        return redirect(url_for("candidate.profile"))
    if ext == ".docx" and not head.startswith(b"PK"):
        flash("This DOCX file is invalid.", "error")
        return redirect(url_for("candidate.profile"))
    resume_file.seek(0, os.SEEK_END)
    size = resume_file.tell()
    resume_file.seek(0)
    if size > 5 * 1024 * 1024:
        flash("Resume must be 5 MB or smaller.", "error")
        return redirect(url_for("candidate.profile"))

    candidate_profile = _get_profile()
    relative_path = save_candidate_file(resume_file, current_user.id, "resume")
    candidate_profile.resume_path = relative_path

    raw_text = ""
    absolute_path = os.path.join(current_app.config["UPLOAD_FOLDER"], relative_path)
    if ext == ".pdf":
        try:
            document = pymupdf.open(absolute_path)
            raw_text = "\n".join(page.get_text() for page in document).strip()
            document.close()
        except Exception:
            current_app.logger.exception("Resume text extraction failed")
    candidate_profile.resume_raw_text = raw_text or None

    resume = Resume(
        candidate_id=current_user.id,
        file_path=relative_path,
        raw_text=raw_text or None,
    )
    db.session.add(resume)
    db.session.commit()
    flash("Resume uploaded successfully.", "success")
    return redirect(url_for("candidate.profile"))


@bp.route("/profile/file/<path:file_path>")
@login_required
@role_required("candidate")
def profile_file(file_path):
    allowed_prefix = f"candidates/{current_user.id}/"
    if not file_path.startswith(allowed_prefix):
        flash("You cannot access that file.", "error")
        return redirect(url_for("candidate.profile"))
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], file_path)
