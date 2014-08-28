import settings
from B2SUtils.email_utils import send_email

def send_html_email(to, subject, content):
    send_email(settings.SERVICE_EMAIL, to, subject, content, settings)
