"""Add apply details and saved jobs.

Revision ID: ab41fdc7e902
Revises: f1b9c4d2a803
"""

from alembic import op
import sqlalchemy as sa


revision = "ab41fdc7e902"
down_revision = "f1b9c4d2a803"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("applications", sa.Column("cover_letter", sa.Text()))
    op.add_column("applications", sa.Column("phone", sa.String(length=20)))
    op.add_column("applications", sa.Column("experience", sa.String(length=50)))
    op.add_column("applications", sa.Column("resume_path", sa.String(length=255)))
    op.add_column("applications", sa.Column("applied_at", sa.DateTime(), server_default=sa.text("now()")))
    op.create_unique_constraint(
        "uq_application_candidate_job",
        "applications",
        ["candidate_id", "job_id"],
    )

    op.create_table(
        "saved_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["candidate_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.UniqueConstraint("candidate_id", "job_id", name="uq_saved_candidate_job"),
    )


def downgrade():
    op.drop_table("saved_jobs")
    op.drop_constraint("uq_application_candidate_job", "applications", type_="unique")
    op.drop_column("applications", "applied_at")
    op.drop_column("applications", "resume_path")
    op.drop_column("applications", "experience")
    op.drop_column("applications", "phone")
    op.drop_column("applications", "cover_letter")
