"""Store channels to check in database

Revision ID: 512ef2b007dc
Revises: b1e5277867b9
Create Date: 2024-07-30 22:46:54.057005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '512ef2b007dc'
down_revision: Union[str, None] = 'b1e5277867b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('channels', sa.Column('check', sa.Boolean(), nullable=False, server_default='true'))
    pass


def downgrade() -> None:
    op.drop_column('channels', 'check')
    pass
