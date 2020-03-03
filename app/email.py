from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)
        app.logger.info("Emails sent to: " + ", ".join(msg.recipients))

def send_email(subject, sender, recipients, text_body, html_body, 
            attachments=None, sync=False):
    current_app.logger.debug(attachments)
    emails_sent_to = []
    for recipient in recipients:
        msg = Message(subject, sender=sender, recipients=[recipient])
        msg.body = text_body
        msg.html = html_body
        if attachments:
            for attachment in attachments:
                msg.attach(*attachment)
        Thread(target=send_async_email, 
                args=(current_app._get_current_object(), msg)).start()
        emails_sent_to += [recipient]
    current_app.logger.info("Trying to send emails to: " + ", ".join(emails_sent_to))
