"""Add candidate profile details and uploaded resume/photo paths.

Revision ID: f1b9c4d2a803
Revises: d7a2c6e4f810
"""

from alembic import op
import sqlalchemy as sa


revision = "f1b9c4d2a803"
down_revision = "d7a2c6e4f810"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("headline", sa.String(length=200)),
        sa.Column("location", sa.String(length=120)),
        sa.Column("phone", sa.String(length=20)),
        sa.Column("gender", sa.String(length=30)),
        sa.Column("birthday", sa.Date()),
        sa.Column("photo_path", sa.String(length=255)),
        sa.Column("resume_path", sa.String(length=255)),
        sa.Column("resume_raw_text", sa.Text()),
        sa.Column("sections", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id"),
    )


def downgrade():
    op.drop_table("candidate_profiles")
