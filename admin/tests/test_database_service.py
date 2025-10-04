from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlmodel import Session, select

from admin.lib.DatabaseService import DatabaseService
from admin.lib.config import DatabaseConfig
from models.telegram import ChannelModel, MediaItem, MediaType, Source, TelegramMetadata


@pytest.fixture
def db_service(tmp_path):
    db_path = tmp_path / "teledeck.db"
    return DatabaseService(DatabaseConfig(db_path=db_path))


def _add_media(session: Session, media_id: str, channel_id: int, message_id: int) -> None:
    item = MediaItem(
        id=media_id,
        source_id=1,
        media_type_id=1,
        file_name=f"{media_id}.dat",
        file_size=1024,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        seen=False,
    )
    metadata = TelegramMetadata(
        media_item_id=media_id,
        channel_id=channel_id,
        message_id=message_id,
        file_id=message_id * 100,
        from_preview=0,
        date=datetime.now(),
        text="",
        url=f"/media/{media_id}",
    )
    session.add(item)
    session.add(metadata)
    session.commit()


def test_database_service_initializes_defaults(db_service):
    with Session(db_service.engine) as session:
        sources = session.exec(select(Source)).all()
        media_types = session.exec(select(MediaType)).all()
        assert {s.name for s in sources} >= {"telegram", "twitter"}
        assert {m.type for m in media_types} >= {"photo", "video"}


def test_get_last_and_earliest_seen_post(db_service):
    with Session(db_service.engine) as session:
        _add_media(session, "item1", channel_id=100, message_id=10)
        _add_media(session, "item2", channel_id=100, message_id=25)

    assert db_service.get_last_seen_post(100) == 25
    assert db_service.get_earliest_seen_post(100) == 10


def test_update_channel_list_sets_flags_without_duplicates(db_service):
    # Seed two channels; only one should remain checked after update
    with Session(db_service.engine) as session:
        session.add(ChannelModel(id=1, title="existing", check=True))
        session.add(ChannelModel(id=2, title="stale", check=True))
        session.commit()

    new_channels = [
        SimpleNamespace(id=1, title="existing"),
        SimpleNamespace(id=3, title="new channel"),
    ]

    db_service.update_channel_list(new_channels)

    with Session(db_service.engine) as session:
        rows = session.exec(select(ChannelModel).order_by(ChannelModel.id)).all()
        assert {c.id for c in rows} == {1, 2, 3}
        assert {c.id for c in rows if c.check} == {1, 3}
        # ensure row for channel 3 created exactly once
        assert len([c for c in rows if c.id == 3]) == 1
