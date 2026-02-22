"""add_user_role_column

Revision ID: 91d0fc16924c
Revises: 0703b58d0198
Create Date: 2026-02-22 10:28:53.185862

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '91d0fc16924c'
down_revision: Union[str, Sequence[str], None] = '0703b58d0198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first
    userrole_enum = sa.Enum('ADMIN', 'MODERATOR', 'USER', name='userrole')
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # Add column as nullable first
    op.add_column('users', sa.Column('role', userrole_enum, nullable=True))

    # Set default value for existing users
    op.execute("UPDATE users SET role = 'USER' WHERE role IS NULL")

    # Now make it non-nullable
    op.alter_column('users', 'role', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')

    # Drop the enum type
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
