import json
import asyncio
from functools import partial
import pathlib
import argparse
from os import environ
from tqdm import tqdm
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, select
from models.telegram import Tag, MediaItem
from admin.lib.TLContext import with_context
from lib.commands import save_forwards, channel_check_list_sync, run_update
from lib.types import ServiceRoutine
from lib.config import Settings


load_dotenv()
cfg = Settings()

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
                print(f"No file found: {name}")



def run_with_context(func: ServiceRoutine):
    async def task():
        t = with_context(cfg, func)
        await t

    asyncio.get_event_loop().run_until_complete(task())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Custom commands')
    parser.add_argument('--add-tags', action='store_true', help='Add tags to the database')
    parser.add_argument('--find-orphans', action='store_true', help='Find files not associated with an entry.')
    parser.add_argument('--save-forwards', help='Find files not associated with an entry.')
    parser.add_argument('--update-channels', action='store_true', help='Update list of channels to check.')
    parser.add_argument('--client-update', action='store_true', help='Pull updates from selected channels')
    args = parser.parse_args()

    if args.add_tags:
        add_tags_to_database()

    elif args.find_orphans:
        directory_path = 'static/media'
        orphan_path = 'recyclebin/orphan'
        find_orphans(pathlib.Path(directory_path), pathlib.Path(orphan_path))

    elif args.save_forwards:
        run_with_context(partial(save_forwards, args.save_forwards))

    elif args.update_channels:
        run_with_context(channel_check_list_sync)

    elif args.client_update:
        run_with_context(run_update)