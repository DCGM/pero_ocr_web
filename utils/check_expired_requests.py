import datetime
import sys
import argparse

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.db import Request, RequestState, DocumentState
from app.mail.mail import send_layout_failed_mail, send_ocr_failed_mail

from config import Config as pero_config


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

    pero_ocr_web_config = vars(pero_config)

    database_url = 'postgres://{}:{}@localhost:5432/{}'.format(args.user, args.password, args.database)
    engine = create_engine(database_url, convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    requests_for_doc = (db_session.query(Request).
                        filter(Request.state == RequestState.IN_PROGRESS).
                        order_by(Request.created_date.desc()))

    newest_requests_for_doc = {}
    for request in requests_for_doc:
        if request.document_id not in newest_requests_for_doc:
            newest_requests_for_doc[request.document_id] = request

    to_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=args.expiration_time)
    expired_requests = []
    for request in newest_requests_for_doc.values():
        if (request.last_processed_page is not None and request.state == RequestState.IN_PROGRESS and request.last_processed_page <= to_time) or request.state == RequestState.IN_PROGRESS_INTERRUPTED:
            expired_requests.append(request)

    print(to_time)
    new_requests = []
    for expired_request in expired_requests:
        if expired_request.previous_attempts < args.job_attempts_limit - 1:
            print("CANCELING", expired_request.id, expired_request.created_date, expired_request.last_processed_page,
                  expired_request.previous_attempts)
            expired_request.state = RequestState.CANCELED
            if 'EMAIL_NOTIFICATION_ADDRESSES' in pero_ocr_web_config and pero_ocr_web_config['EMAIL_NOTIFICATION_ADDRESSES']:
                if expired_request.layout_id is not None:
                    send_layout_failed_mail(pero_ocr_web_config, expired_request, canceled=True)
                else:
                    send_ocr_failed_mail(pero_ocr_web_config, expired_request, canceled=True)
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
        elif expired_request.previous_attempts == args.job_attempts_limit - 1:
            if expired_request.state != RequestState.FAILURE:
                print("SETTING TO FAILURE", expired_request.id, expired_request.created_date, expired_request.last_processed_page,
                      expired_request.previous_attempts)
                expired_request.state = RequestState.FAILURE
                if expired_request.layout_id is not None:
                    expired_request.document.state = DocumentState.NEW
                    if 'EMAIL_NOTIFICATION_ADDRESSES' in pero_ocr_web_config and pero_ocr_web_config['EMAIL_NOTIFICATION_ADDRESSES']:
                        send_layout_failed_mail(pero_ocr_web_config, expired_request)
                elif expired_request.baseline_id is not None:
                    expired_request.document.state = DocumentState.COMPLETED_LAYOUT_ANALYSIS
                    if 'EMAIL_NOTIFICATION_ADDRESSES' in pero_ocr_web_config and pero_ocr_web_config['EMAIL_NOTIFICATION_ADDRESSES']:
                        send_ocr_failed_mail(pero_ocr_web_config, expired_request)
                else:
                    expired_request.document.state = DocumentState.COMPLETED_OCR
                    if 'EMAIL_NOTIFICATION_ADDRESSES' in pero_ocr_web_config and pero_ocr_web_config['EMAIL_NOTIFICATION_ADDRESSES']:
                        send_ocr_failed_mail(pero_ocr_web_config, expired_request)
        else:
            pass

    if expired_requests:
        db_session.add_all(new_requests)
        db_session.commit()


if __name__ == '__main__':
    sys.exit(main())
