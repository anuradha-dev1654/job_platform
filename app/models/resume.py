
from app.extensions import db
from pgvector.sqlalchemy import Vector


EMBEDDING_DIM = 768


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)

    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    file_path = db.Column(db.String(255), nullable=False)
    raw_text = db.Column(db.Text)

    embedding = db.Column(Vector(EMBEDDING_DIM))

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
# TODO: resume model
