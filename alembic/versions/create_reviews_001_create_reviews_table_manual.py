"""create_reviews_table_manual

Revision ID: create_reviews_001
Revises: 7dd2855e986b
Create Date: 2026-02-23 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'create_reviews_001'
down_revision: Union[str, Sequence[str], None] = '7dd2855e986b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reviews table."""
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.String(length=1000), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('book_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='reviews_user_id_fkey'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], name='reviews_book_id_fkey'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range')
    )
    op.create_index('ix_reviews_uuid', 'reviews', ['uuid'], unique=True)


def downgrade() -> None:
    """Drop reviews table."""
    op.drop_index('ix_reviews_uuid', table_name='reviews')
    op.drop_table('reviews')
