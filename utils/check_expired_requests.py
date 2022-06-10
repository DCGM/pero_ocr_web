import datetime
import sys
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import func

from app.db import Request, RequestState
from pprint import pprint


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', type=str, default='postgres')
    parser.add_argument('-p', '--password', type=str, default='pero')
    parser.add_argument('-d', '--database', type=str, required=True, help="Database.")
    parser.add_argument('-e', '--expiration-time', type=int, default=5, help="Minimal time for expiration.")
    parser.add_argument('-a', '--job-attempts-limit', type=int, default=4, help="Maximum attempts for one job.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    database_url = 'postgresql://{}:{}@localhost:5432/{}'.format(args.user, args.password, args.database)
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    to_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=args.expiration_time)
    expired_requests = db_session.query(Request).filter(Request.last_processed_page <= to_time,
                                                        Request.state != RequestState.PENDING,
                                                        Request.state != RequestState.SUCCESS,
                                                        Request.state != RequestState.CANCELED).order_by(Request.created_date.desc())

    newest_expired_requests_for_doc = {}
    for expired_request in expired_requests:
        if expired_request.document_id not in newest_expired_requests_for_doc:
            newest_expired_requests_for_doc[expired_request.document_id] = expired_request
    expired_requests = newest_expired_requests_for_doc.values()

    print(to_time)
    new_requests = []
    for expired_request in expired_requests:
        print("CANCELING", expired_request.id, expired_request.created_date, expired_request.last_processed_page,
              expired_request.previous_attempts)
        expired_request.state = RequestState.CANCELED
        if expired_request.previous_attempts < args.job_attempts_limit - 1:
            print("CREATING NEW REQUEST")
            new_request = Request(layout_id=expired_request.layout_id,
                                  baseline_id=expired_request.baseline_id,
                                  ocr_id=expired_request.ocr_id,
                                  language_model_id=expired_request.language_model_id,
                                  request_type=expired_request.request_type,
                                  state=RequestState.PENDING,
                                  document_id=expired_request.document_id,
                                  previous_attempts=expired_request.previous_attempts + 1)
            new_requests.append(new_request)
    if expired_requests:
        db_session.add_all(new_requests)
        db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
