import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import LanguageModel


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database to register language model engines.")
    parser.add_argument('-r', '--replace', action="store_true", help="Replace all language model engines.")
    args = parser.parse_args()
    return args


language_model_engines = [
    {"name": "NONE", "description": "Don't use any language model."}
]


def main():
    args = parseargs()

    database_url = 'sqlite:///' + args.database
    engine = create_engine(database_url, convert_unicode=True, connect_args={'check_same_thread': False})
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))

    if args.replace:
        for db_language_model in db_session.query(LanguageModel).all():
            db_language_model.active = False
        db_session.commit()

    for language_model in language_model_engines:
        if db_session.query(LanguageModel).filter(LanguageModel.name == language_model['name']).filter(LanguageModel.active == True).first() is None:
            db_language_model = LanguageModel(**language_model)
            db_session.add(db_language_model)
            print('ADDED ', language_model)
        else:
            print('SKIPPING', language_model)

    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
