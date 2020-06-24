import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import Baseline


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database to register baseline engines.")
    parser.add_argument('-r', '--replace', action="store_true", help="Replace all baseline engines.")
    args = parser.parse_args()
    return args


baseline_engines = [
    {"name": "Universal", "description": "Universal baseline detector that should work on majority of documents."},
    {"name": "Experimental", "description": "Experimental baseline detector that should work on majority of documents (under development)."}
]


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    if args.replace:
        for db_baseline in db_session.query(Baseline).all():
            db_baseline.active = False
        db_session.commit()

    for baseline in baseline_engines:
        if db_session.query(Baseline).filter(Baseline.name == baseline['name']).filter(Baseline.active == True).first() is None:
            db_baseline = Baseline(**baseline)
            db_session.add(db_baseline)
            print('ADDED ', baseline)
        else:
            print('SKIPPING', baseline)

    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
