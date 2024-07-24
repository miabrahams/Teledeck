"""Separate metadata and tags

Revision ID: 0ed761b5d4f7
Revises:
Create Date: 2024-07-23 21:09:06.674845

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0ed761b5d4f7"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.rename_table("media_items", "old_media_items")

    # Create new tables
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "media_items",
        # sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("sequential_id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("media_type_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("seen", sa.Boolean(), nullable=False),
        sa.Column("favorite", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("user_deleted", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
        ),
        sa.ForeignKeyConstraint(
            ["media_type_id"],
            ["media_types.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "media_item_duplicates",
        sa.Column("first", sa.String(length=36), nullable=False),
        sa.Column("second", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["first"],
            ["media_items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["second"],
            ["media_items.id"],
        ),
        sa.UniqueConstraint("first", "second"),
    )

    op.create_table(
        "media_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type"),
    )

    op.create_table(
        "telegram_metadata",
        sa.Column("media_item_id", sa.String(length=36), nullable=False),
        sa.Column("channel_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("from_preview", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.ForeignKeyConstraint( ["media_item_id"], ["media_items.id"],),
        sa.ForeignKeyConstraint( ["channel_id"], ["channels.id"],),
        sa.PrimaryKeyConstraint("media_item_id"),
    )

    op.create_table(
        "twitter_metadata",
        sa.Column("media_item_id", sa.String(length=36), nullable=False),
        sa.Column("tweet_id", sa.Integer, nullable=False),
        sa.Column("username", sa.String(length=36), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_item_id"],
            ["media_items.id"],
        ),
        sa.PrimaryKeyConstraint("media_item_id"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "media_item_tags",
        sa.Column("media_item_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["media_item_id"],
            ["media_items.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
        ),
        sa.PrimaryKeyConstraint("media_item_id", "tag_id"),
    )

    # Insert 'telegram' into sources
    op.execute(
        "INSERT INTO sources (name) VALUES ('telegram'), ('twitter'), ('furaffinity'), ('deviantart'), ('e621');"
    )

    op.execute(
        "INSERT INTO media_types (type) VALUES ('photo'), ('video'), ('jpeg'), ('webp'), ('gif'), ('png'), ('document'), ('image');"
    )

    # Migrate data from old_media_items to new tables
    op.execute("""
        INSERT INTO media_items (id, source_id, sequential_id, media_type_id, file_name, file_size, created_at, updated_at, seen, favorite, user_deleted)
        SELECT hex(randomblob(16)),
               (SELECT id FROM sources WHERE name = 'telegram'),
               o.id,
               mt.id,
               o.file_name, o.file_size, o.date, o.date, o.seen, o.favorite, o.user_deleted
        FROM old_media_items o
        JOIN media_types mt ON o.type = mt.type
    """)

    op.execute("""
        INSERT INTO telegram_metadata (media_item_id, channel_id, message_id, file_id, from_preview, date, text, url)
        SELECT m.id, o.channel_id, o.message_id, ABS(o.file_id),
            CASE WHEN o.file_id < 0 THEN 1 ELSE 0 END,
            o.date, o.text, o.url
        FROM media_items m
        JOIN old_media_items o ON m.sequential_id = o.id
    """)

    op.drop_table("old_media_items")

    # op.create_index('ix_media_items_source_id', 'media_items', ['source_id'], unique=False)


def downgrade():
    raise NotImplementedError(""" WARNING: This migration involves significant schema changes. A full automatic downgrade is not possible.""")