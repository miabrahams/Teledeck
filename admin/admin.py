import json
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine.base import Engine
from dotenv import load_dotenv
import pathlib
from models.telegram import Tag, MediaItem
import argparse
from os import environ
from tqdm import tqdm

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Custom commands')
    parser.add_argument('--add-tags', action='store_true', help='Add tags to the database')
    parser.add_argument('--find-orphans', action='store_true', help='Find files not associated with an entry.')
    args = parser.parse_args()

    if args.add_tags:
        add_tags_to_database()

    if args.find_orphans:
        directory_path = 'static/media'
        orphan_path = 'recyclebin/orphan'
        find_orphans(pathlib.Path(directory_path), pathlib.Path(orphan_path))