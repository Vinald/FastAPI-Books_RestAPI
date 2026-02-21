"""add_id_primary_key_to_tables

Revision ID: 97654229837b
Revises: 554db8f462ac
Create Date: 2026-02-21 20:32:13.905275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97654229837b'
down_revision: Union[str, Sequence[str], None] = '554db8f462ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add id column as SERIAL (auto-increment) to books table
    # Using raw SQL to properly handle existing data
    op.execute('ALTER TABLE books ADD COLUMN id SERIAL')
    op.execute('ALTER TABLE books DROP CONSTRAINT IF EXISTS books_pkey')
    op.execute('ALTER TABLE books ADD PRIMARY KEY (id)')
    op.create_unique_constraint('books_uuid_key', 'books', ['uuid'])

    # Add id column as SERIAL (auto-increment) to users table
    op.execute('ALTER TABLE users ADD COLUMN id SERIAL')
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey')
    op.execute('ALTER TABLE users ADD PRIMARY KEY (id)')
    op.create_unique_constraint('users_uuid_key', 'users', ['uuid'])


def downgrade() -> None:
    """Downgrade schema."""
    # Revert users table
    op.drop_constraint('users_uuid_key', 'users', type_='unique')
    op.execute('ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey')
    op.drop_column('users', 'id')
    op.execute('ALTER TABLE users ADD PRIMARY KEY (uuid)')

    # Revert books table
    op.drop_constraint('books_uuid_key', 'books', type_='unique')
    op.execute('ALTER TABLE books DROP CONSTRAINT IF EXISTS books_pkey')
    op.drop_column('books', 'id')
    op.execute('ALTER TABLE books ADD PRIMARY KEY (uuid)')
