"""Add company profile and detailed job fields.

Revision ID: cc31d0e7c904
Revises: ab41fdc7e902
"""

from alembic import op
import sqlalchemy as sa


revision = "cc31d0e7c904"
down_revision = "ab41fdc7e902"
branch_labels = None
depends_on = None


def upgrade():
    for name, column in (
        ("salary", sa.String(length=120)),
        ("experience", sa.String(length=80)),
        ("openings", sa.Integer()),
        ("role", sa.String(length=120)),
        ("industry", sa.String(length=180)),
        ("department", sa.String(length=120)),
        ("employment_type", sa.String(length=80)),
        ("role_category", sa.String(length=120)),
        ("ug_qualification", sa.String(length=250)),
        ("pg_qualification", sa.String(length=250)),
        ("key_skills", sa.JSON()),
    ):
        op.add_column("jobs", sa.Column(name, column))

    op.alter_column("jobs", "openings", server_default="1")
    op.alter_column("jobs", "key_skills", server_default=sa.text("'[]'::json"))

    for name, column in (
        ("description", sa.Text()),
        ("industry", sa.String(length=180)),
        ("company_size", sa.String(length=80)),
        ("founded_year", sa.Integer()),
        ("rating", sa.Float()),
        ("reviews_count", sa.Integer()),
        ("benefits", sa.JSON()),
    ):
        op.add_column("companies", sa.Column(name, column))
    op.alter_column("companies", "reviews_count", server_default="0")
    op.alter_column("companies", "benefits", server_default=sa.text("'[]'::json"))


def downgrade():
    for name in ("benefits", "reviews_count", "rating", "founded_year",
                 "company_size", "industry", "description"):
        op.drop_column("companies", name)
    for name in ("key_skills", "pg_qualification", "ug_qualification",
                 "role_category", "employment_type", "department", "industry",
                 "role", "openings", "experience", "salary"):
        op.drop_column("jobs", name)
