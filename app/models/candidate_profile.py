from app.extensions import db


class CandidateProfile(db.Model):
    __tablename__ = "candidate_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    headline = db.Column(db.String(200))
    location = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(30))
    birthday = db.Column(db.Date)
    photo_path = db.Column(db.String(255))
    resume_path = db.Column(db.String(255))
    resume_raw_text = db.Column(db.Text)
    sections = db.Column(db.JSON, default=dict, nullable=False)

    user = db.relationship("User", backref=db.backref("candidate_profile", uselist=False))
