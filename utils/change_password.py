import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import argparse
from app.db import User
from werkzeug.security import generate_password_hash


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-e', '--email', type=str, required=True, help="Email of user.")
    parser.add_argument('-p', '--new-password', type=str, required=True, help="New password for user.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'postgres://postgres:pero@localhost:5432/' + args.database
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    user = db_session.query(User).filter(User.email == args.email).first()
    user.password = generate_password_hash(args.new_password)
    db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
