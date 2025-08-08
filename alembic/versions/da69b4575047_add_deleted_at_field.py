"""add_deleted_at_field

Revision ID: da69b4575047
Revises: 004318c1c5a6
Create Date: 2025-08-07 22:34:04.037784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'da69b4575047'
down_revision: Union[str, None] = '004318c1c5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add deleted_at column to media_items table
    op.add_column('media_items', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add index for the deleted_at column for better performance
    op.create_index('ix_media_items_deleted_at', 'media_items', ['deleted_at'])


def downgrade() -> None:
    # Remove the index first
    op.drop_index('ix_media_items_deleted_at', table_name='media_items')
    
    # Remove the deleted_at column
    op.drop_column('media_items', 'deleted_at')
