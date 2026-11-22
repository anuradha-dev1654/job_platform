
from app.extensions import db
from pgvector.sqlalchemy import Vector


EMBEDDING_DIM = 768


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(120))
    salary = db.Column(db.String(120))
    experience = db.Column(db.String(80))
    openings = db.Column(db.Integer, default=1)
    role = db.Column(db.String(120))
    industry = db.Column(db.String(180))
    department = db.Column(db.String(120))
    employment_type = db.Column(db.String(80))
    role_category = db.Column(db.String(120))
    ug_qualification = db.Column(db.String(250))
    pg_qualification = db.Column(db.String(250))
    key_skills = db.Column(db.JSON, default=list)

    embedding = db.Column(Vector(EMBEDDING_DIM))

    created_at = db.Column(db.DateTime, server_default=db.func.now())
