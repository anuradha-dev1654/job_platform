"""Allow the current company registration model to omit legacy credentials.

Revision ID: d7a2c6e4f810
Revises: c2f4d8b7a901
"""

from alembic import op


revision = "d7a2c6e4f810"
down_revision = "c2f4d8b7a901"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("companies", "email", nullable=True)
    op.alter_column("companies", "password_hash", nullable=True)


def downgrade():
    op.alter_column("companies", "password_hash", nullable=False)
    op.alter_column("companies", "email", nullable=False)
