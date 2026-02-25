"""add is_verified column to users

Revision ID: add_is_verified_001
Revises: create_reviews_001
Create Date: 2026-02-25 20:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'add_is_verified_001'
down_revision: Union[str, Sequence[str], None] = 'create_reviews_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_verified column to users table."""
    op.add_column(
        'users',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove is_verified column from users table."""
    op.drop_column('users', 'is_verified')
