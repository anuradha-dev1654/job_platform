from app.extensions import db


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean, default=False)
    trust_score = db.Column(db.Integer)  # from fake_company_detector
