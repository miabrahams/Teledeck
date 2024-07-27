import json
from sqlmodel import create_engine, Session, select
from dotenv import load_dotenv
import pathlib
from models.telegram import Tag, MediaItem
import argparse
from os import environ
from tqdm import tqdm
from lib.tl_client import get_context, get_messages, extract_forward
from telethon.utils import resolve_id, get_peer_id
from telethon import functions, types, hints, tl
from telethon.tl.custom.dialog import Dialog
import asyncio
from typing import cast


load_dotenv()

engine = create_engine("sqlite:///" + environ['DB_PATH'])

def add_tags_to_database():
    with open('tagger/model/tags_8041.json') as tagfile:
        tags = json.load(tagfile)
        with Session(engine) as session:
            for tag in tags:
                session.add(Tag(name=tag))
            session.commit()
    with open('tagger/model/tags_extra.json') as tagfile:
        tags = json.load(tagfile)
        with Session(engine) as session:
            for (_, tag) in tags:
                session.add(Tag(name=tag))
            session.commit()



def find_orphans(media_path: pathlib.Path, orphan_path: pathlib.Path):
    """Find and print orphans in the specified directory."""
    # files_by_size: Dict[int, List[DirEntry[str]]] = {}
    # duplicates: List[str] = []
    # n = 0

    for item in tqdm(media_path.glob('*')):
        if not item.is_file():
            continue
        name = item.parts[-1]
        with Session(engine) as session:
            result = session.exec(select(MediaItem).where(MediaItem.file_name == name)).first()
            if not result:
                print("Would like to move to: " + str(orphan_path.joinpath(name)))
                item.rename(orphan_path.joinpath(name))
                print(f"No file found: {name}" )

async def save_forwards(chat_name: str):
    ctx = await get_context()
    # resolved = get_peer_id(chat_id)
    entity: Optional[hints.Entity] = None
    async for d in ctx.tclient.iter_dialogs():
        dialog = cast(Dialog, d)
        if dialog.name == chat_name:
            entity: hints.Entity = dialog.entity
            break
    if not entity:
        print("Could not find chat.")

    n = 0
    async for message in ctx.tclient.iter_messages(entity, limit=5000):
        try:
            await extract_forward(ctx, message)
        except Exception as e:
            print(e)
        n += 1
        print(n)

    ctx.save_data()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Custom commands')
    parser.add_argument('--add-tags', action='store_true', help='Add tags to the database')
    parser.add_argument('--find-orphans', action='store_true', help='Find files not associated with an entry.')
    parser.add_argument('--save-forwards', help='Find files not associated with an entry.')
    args = parser.parse_args()

    if args.add_tags:
        add_tags_to_database()

    elif args.find_orphans:
        directory_path = 'static/media'
        orphan_path = 'recyclebin/orphan'
        find_orphans(pathlib.Path(directory_path), pathlib.Path(orphan_path))

    elif args.save_forwards:
        asyncio.get_event_loop().run_until_complete(save_forwards(args.save_forwards))