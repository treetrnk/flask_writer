from flask import current_app
from flask_mail import Message
from app import mail

def send_email(subject, sender, recipients, text_body, html_body, 
            attachments=None, sync=False):
    with mail.connect() as conn:
        for recipient in recipients:
            msg = Message(subject, sender=sender, recipients=recipients)
            msg.body = text_body
            msg.html = html_body
            if attachments:
                for attachment in attachments:
                    msg.attach(*attachment)
            conn.send(msg)
