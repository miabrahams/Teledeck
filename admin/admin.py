import json
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine.base import Engine
from dotenv import load_dotenv
import os
from models.telegram import Tag
import argparse

load_dotenv()

engine = create_engine("sqlite:///" + os.environ['DB_PATH'])

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





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Custom commands')
    parser.add_argument('--add_tags', action='store_true', help='Add tags to the database')
    args = parser.parse_args()

    if args.add_tags:
        add_tags_to_database()