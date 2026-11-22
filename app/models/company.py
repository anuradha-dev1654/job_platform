from app.extensions import db


class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(255))
    is_approved = db.Column(db.Boolean, default=False)
    trust_score = db.Column(db.Integer)

    # company registration wizard fields
    rep_designation = db.Column(db.String(80))
    corporate_id_type = db.Column(db.String(10))   # CIN / GST / PAN
    corporate_id = db.Column(db.String(30), unique=True)
    business_type = db.Column(db.String(60))
    address = db.Column(db.Text)
    city = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    documents = db.Column(db.JSON, default=dict)
    description = db.Column(db.Text)
    industry = db.Column(db.String(180))
    company_size = db.Column(db.String(80))
    founded_year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    reviews_count = db.Column(db.Integer, default=0)
    benefits = db.Column(db.JSON, default=list)
    logo_path = db.Column(db.String(255))

    user = db.relationship("User", backref=db.backref("company", uselist=False))