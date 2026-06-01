"""add is_active to users

Revision ID: c7a1f2e9b4d0
Revises: 63f60d4f8558
Create Date: 2026-06-01 07:15:00.000000

The User model declares is_active (Boolean, default=True, indexed) but the
initial schema migrations predate it, leaving the live users table without
the column. This migration closes that drift so /auth/login stops 500ing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a1f2e9b4d0'
down_revision: Union[str, Sequence[str], None] = '63f60d4f8558'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # server_default backfills existing rows; NOT NULL matches the model.
    op.add_column(
        'users',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index('ix_users_is_active', 'users', ['is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_users_is_active', table_name='users')
    op.drop_column('users', 'is_active')
