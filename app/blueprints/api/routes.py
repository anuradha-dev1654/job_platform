from flask import jsonify
from flask import request
from . import bp
from app.extensions import db
from app.models import Job, Company


@bp.route("/health")
def health():
    return jsonify(status="ok")


@bp.route("/locations")
def locations():
    q = request.args.get("q", "").strip()
    values = set()

    job_query = db.select(Job.location).where(Job.location.isnot(None)).distinct()
    company_query = db.select(Company.city).where(Company.city.isnot(None)).distinct()
    if q:
        job_query = job_query.where(Job.location.ilike(f"%{q}%"))
        company_query = company_query.where(Company.city.ilike(f"%{q}%"))

    for value in db.session.scalars(job_query.limit(30)):
        if value:
            values.add(value.strip())
    for value in db.session.scalars(company_query.limit(30)):
        if value:
            values.add(value.strip())

    if not q:
        values.update(["Remote", "Ahmedabad", "Bengaluru", "Delhi", "Mumbai", "Pune"])
    else:
        values = {value for value in values if q.lower() in value.lower()}

    return jsonify(locations=sorted(values)[:30])
