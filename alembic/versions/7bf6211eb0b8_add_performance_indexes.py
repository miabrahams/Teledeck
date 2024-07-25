"""Add performance indexes

Revision ID: 7bf6211eb0b8
Revises: 0ed761b5d4f7
Create Date: 2024-07-25 15:13:33.635990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bf6211eb0b8'
down_revision: Union[str, None] = '0ed761b5d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index('idx_media_items_created_at', 'media_items', ['created_at'])
    op.create_index('idx_media_items_file_size', 'media_items', ['file_size'])
    op.create_index('idx_media_items_favorite', 'media_items', ['favorite'])
    op.create_index('idx_media_items_user_deleted', 'media_items', ['user_deleted'])
    op.create_index('idx_media_items_seen', 'media_items', ['seen'])

    op.create_index('idx_media_item_tags_tag_id', 'media_item_tags', ['tag_id'])
    op.create_index('idx_media_item_tags_weight', 'media_item_tags', ['weight'])

    op.drop_column('media_items', 'file_path')
    op.drop_column('media_items', 'sequential_id')


def downgrade():
    op.drop_index('idx_media_items_created_at', table_name='media_items')
    op.drop_index('idx_media_items_file_size', table_name='media_items')
    op.drop_index('idx_media_items_favorite', table_name='media_items')
    op.drop_index('idx_media_items_user_deleted', table_name='media_items')
    op.drop_index('idx_media_items_seen', table_name='media_items')

    op.drop_index('idx_media_item_tags_tag_id', table_name='media_item_tags')
    op.drop_index('idx_media_item_tags_weight', table_name='media_item_tags')