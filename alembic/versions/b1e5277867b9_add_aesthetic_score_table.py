"""Add aesthetic score table

Revision ID: b1e5277867b9
Revises: 7bf6211eb0b8
Create Date: 2024-07-28 18:55:42.563365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e5277867b9'
down_revision: Union[str, None] = '7bf6211eb0b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'aesthetic_score',
        sa.Column('media_item_id', sa.String(length=36), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['media_item_id'], ['media_items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('media_item_id'),
    )
    pass


def downgrade() -> None:
    op.drop_table('aesthetic_score')
    pass
