"""Add company logo path.

Revision ID: e91ca2c9d702
Revises: cc31d0e7c904
"""

from alembic import op
import sqlalchemy as sa


revision = "e91ca2c9d702"
down_revision = "cc31d0e7c904"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("companies", sa.Column("logo_path", sa.String(length=255)))


def downgrade():
    op.drop_column("companies", "logo_path")
