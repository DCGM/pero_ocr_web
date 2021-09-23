from drymail import SMTPMailer, Message
from flask import current_app
import traceback


def send_mail(subject, body, sender, recipients, host):
    client = SMTPMailer(host=host)
    message = Message(subject=subject, sender=sender, receivers=recipients, html=body)
    print()
    print("SENDING MAIL")
    print()
    print(message)
    print()
    client.send(message)


def send_internal_server_error_mail():
    send_mail(subject="PERO OCR - WEB Bot - INTERNAL SERVER ERROR",
              body=traceback.format_exc().replace("\n", "<br>"),
              sender=('PERO OCR - WEB Bot', current_app.config['MAIL_SENDER']),
              recipients=current_app.config['EMAIL_NOTIFICATION_ADDRESSES'],
              host=current_app.config['MAIL_SERVER'])


def send_layout_failed_mail(layout_request, request):
    document = layout_request.document
    user = document.user
    layout_detector = layout_request.layout_detector

    message_body = "processing_client_hostname: {}<br>" \
                   "document_id: {}<br>" \
                   "document_name: {}<br>" \
                   "user_id: {}<br>" \
                   "user_name: {} {}<br>" \
                   "user_email: {}<br>" \
                   "layout_detector_id: {}<br>" \
                   "layout_detector_name: {}<br>" \
                   "request_id: {}<br><br>" \
                   "parse_folder.py log<br>" \
                   "########################################<br><br>{}" \
                   "<br>########################################" \
        .format(request.host,
                document.id,
                document.name,
                user.id,
                user.first_name,
                user.last_name,
                user.email,
                layout_detector.id,
                layout_detector.name,
                layout_request.id,
                layout_request.log.replace("\n", "<br>"))

    send_mail(subject="PERO OCR - WEB Bot - LAYOUT PROCESSING FAILED",
              body=message_body,
              sender=('PERO OCR - WEB Bot', current_app.config['MAIL_SENDER']),
              recipients=current_app.config['EMAIL_NOTIFICATION_ADDRESSES'],
              host=current_app.config['MAIL_SERVER'])


def send_ocr_failed_mail(ocr_request, request):
    document = ocr_request.document
    user = document.user
    baseline = ocr_request.baseline
    ocr = ocr_request.ocr
    language_model = ocr_request.language_model

    if language_model is None:
        language_model_id = "NONE"
        language_model_name = "NONE"
    else:
        language_model_id = language_model.id
        language_model_name = language_model.name

    message_body = "processing_client_hostname: {}<br>" \
                   "document_id: {}<br>" \
                   "document_name: {}<br>" \
                   "user_id: {}<br>" \
                   "user_name: {} {}<br>" \
                   "user_email: {}<br>" \
                   "baseline_id: {}<br>" \
                   "baseline_name: {}<br>" \
                   "ocr_id: {}<br>" \
                   "ocr_name: {}<br>" \
                   "language_model_id: {}<br>" \
                   "language_model_name: {}<br>" \
                   "request_id: {}<br><br>" \
                   "parse_folder.py log<br>" \
                   "########################################<br><br>{}" \
                   "<br>########################################" \
        .format(request.host,
                document.id,
                document.name,
                user.id,
                user.first_name,
                user.last_name,
                user.email,
                baseline.id,
                baseline.name,
                ocr.id,
                ocr.name,
                language_model_id,
                language_model_name,
                ocr_request.id,
                ocr_request.log.replace("\n", "<br>"))

    send_mail(subject="PERO OCR - WEB Bot - OCR PROCESSING FAILED",
              body=message_body,
              sender=('PERO OCR - WEB Bot', current_app.config['MAIL_SENDER']),
              recipients=current_app.config['EMAIL_NOTIFICATION_ADDRESSES'],
              host=current_app.config['MAIL_SERVER'])

