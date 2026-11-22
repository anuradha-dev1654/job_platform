"""Synchronize the database with the current user and company models.

Revision ID: c2f4d8b7a901
Revises: ead59b5853d3
"""

from alembic import op
import sqlalchemy as sa


revision = "c2f4d8b7a901"
down_revision = "ead59b5853d3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="candidate"),
        sa.Column("github_username", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.add_column("companies", sa.Column("user_id", sa.Integer(), nullable=True))
    op.add_column("companies", sa.Column("rep_designation", sa.String(length=80)))
    op.add_column("companies", sa.Column("corporate_id_type", sa.String(length=10)))
    op.add_column("companies", sa.Column("corporate_id", sa.String(length=30)))
    op.add_column("companies", sa.Column("business_type", sa.String(length=60)))
    op.add_column("companies", sa.Column("address", sa.Text()))
    op.add_column("companies", sa.Column("city", sa.String(length=80)))
    op.add_column("companies", sa.Column("phone", sa.String(length=20)))
    op.add_column("companies", sa.Column("documents", sa.JSON(), server_default=sa.text("'{}'::json")))

    op.create_foreign_key(
        "fk_companies_user_id_users",
        "companies",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_unique_constraint("uq_companies_user_id", "companies", ["user_id"])
    op.create_unique_constraint("uq_companies_corporate_id", "companies", ["corporate_id"])
    op.alter_column("companies", "user_id", nullable=False)

    op.drop_constraint("resumes_candidate_id_fkey", "resumes", type_="foreignkey")
    op.create_foreign_key(
        "fk_resumes_candidate_id_users",
        "resumes",
        "users",
        ["candidate_id"],
        ["id"],
    )
    op.drop_constraint("applications_candidate_id_fkey", "applications", type_="foreignkey")
    op.create_foreign_key(
        "fk_applications_candidate_id_users",
        "applications",
        "users",
        ["candidate_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_applications_candidate_id_users", "applications", type_="foreignkey")
    op.create_foreign_key(
        "applications_candidate_id_fkey",
        "applications",
        "candidates",
        ["candidate_id"],
        ["id"],
    )
    op.drop_constraint("fk_resumes_candidate_id_users", "resumes", type_="foreignkey")
    op.create_foreign_key(
        "resumes_candidate_id_fkey",
        "resumes",
        "candidates",
        ["candidate_id"],
        ["id"],
    )
    op.drop_constraint("uq_companies_corporate_id", "companies", type_="unique")
    op.drop_constraint("uq_companies_user_id", "companies", type_="unique")
    op.drop_constraint("fk_companies_user_id_users", "companies", type_="foreignkey")
    for column in (
        "user_id",
        "rep_designation",
        "corporate_id_type",
        "corporate_id",
        "business_type",
        "address",
        "city",
        "phone",
        "documents",
    ):
        op.drop_column("companies", column)
    op.drop_table("users")
