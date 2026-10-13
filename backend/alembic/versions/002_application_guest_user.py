"""Allow guest applications (nullable user_id)

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from sqlalchemy.dialects import postgresql

from alembic import op

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guest applications are submitted before a user account exists, so the
    # user_id must be nullable and linked later when the user registers.
    op.alter_column(
        'applications',
        'user_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'applications',
        'user_id',
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
