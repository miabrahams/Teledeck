import json
import asyncio
from functools import partial
from pathlib import Path
import argparse
from tqdm import tqdm
from dotenv import load_dotenv
from sqlmodel import create_engine, Session, select
from sqlalchemy import Engine
from models.telegram import Tag, MediaItem
from admin.lib.TLContext import with_context
from lib.commands import save_forwards, channel_check_list_sync, run_update, run_export
from lib.types import ServiceRoutine
from lib.config import Settings, create_export_overrides


load_dotenv()


# TODO: Move to DatabaseService
def add_tags_to_database(engine: Engine):
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

def find_orphans(engine: Engine, media_path: Path, orphan_path: Path):
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



def run_with_context(cfg: Settings, func: ServiceRoutine):
    async def task():
        await with_context(cfg, func)

    asyncio.get_event_loop().run_until_complete(task())

def setup_argparse():
    parser = argparse.ArgumentParser(description='Custom commands')
    parser.add_argument('--add-tags', action='store_true', help='Add tags to the database')
    parser.add_argument('--find-orphans', action='store_true', help='Find files not associated with an entry.')
    parser.add_argument('--save-forwards', help='Find files not associated with an entry.')
    parser.add_argument('--update-channels', action='store_true', help='Update list of channels to check.')
    parser.add_argument('--client-update', action='store_true', help='Pull updates from selected channels')
    parser.add_argument('--export-channel', type=str, help='Export all messages from specified channel name to separate database')
    parser.add_argument('--export-path', type=str, help='Path for exported channel data')
    return parser

if __name__ == '__main__':
    parser = setup_argparse()
    args = parser.parse_args()
    cfg = Settings()

    if args.add_tags:
        engine = create_engine(f"sqlite:///{cfg.DB_PATH}")
        add_tags_to_database(engine)

    elif args.find_orphans:
        directory_path = 'static/media'
        orphan_path = 'recyclebin/orphan'
        engine = create_engine(f"sqlite:///{cfg.DB_PATH}")
        find_orphans(engine, Path(directory_path), Path(orphan_path))

    elif args.save_forwards:
        run_with_context(cfg, partial(save_forwards, args.save_forwards))

    elif args.update_channels:
        run_with_context(cfg, channel_check_list_sync)

    elif args.client_update:
        run_with_context(cfg, run_update)

    elif args.export_channel:
        export_path = Path(args.export_path) if args.export_path else cfg.EXPORT_PATH / str(args.export_channel)
        overrides = create_export_overrides(args.export_channel, Path(args.export_path), cfg)
        run_with_context(overrides, partial(run_export, args.export_channel))