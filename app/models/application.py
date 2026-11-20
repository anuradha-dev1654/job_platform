from app.extensions import db


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    match_score = db.Column(db.Float)
    status = db.Column(db.String(30), default="applied")  # applied/shortlisted/rejected
