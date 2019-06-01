from flask_mail import Message
from app import mail

def send_email(page, subject, recipients, text_body, html_body)
    for recipient in recipients:
        msg = Message(subject, sender='no-reply@houstonhare.com', recipients=recipient)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
