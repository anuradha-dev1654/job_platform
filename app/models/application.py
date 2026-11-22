from app.extensions import db


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    match_score = db.Column(db.Float)
    status = db.Column(db.String(30), default="applied")  # applied/shortlisted/rejected
    cover_letter = db.Column(db.Text)
    phone = db.Column(db.String(20))
    experience = db.Column(db.String(50))
    resume_path = db.Column(db.String(255))
    applied_at = db.Column(db.DateTime, server_default=db.func.now())

    __table_args__ = (db.UniqueConstraint("candidate_id", "job_id", name="uq_application_candidate_job"),)
