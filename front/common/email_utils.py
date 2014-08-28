import settings

from common.m17n import trans_func
from common.utils import gen_html_body
from B2SUtils.email_utils import send_email

def send_new_user_email(to_addr, data):
    if not settings.SEND_EMAILS:
        return
    subject = trans_func('NEW_USER_EMAIL_SUBJECT') \
              % {'brand': settings.BRAND_NAME}
    content = gen_html_body('new_user_email.html', data, layout=None)
    send_email(settings.SERVICE_EMAIL, to_addr, subject, content, settings)

def send_order_email(to_addr, data):
    if not settings.SEND_EMAILS:
        return
    subject = trans_func('ORDER_EMAIL_SUBJECT')
    content = gen_html_body('order_email.html', data, layout=None)
    send_email(settings.SERVICE_EMAIL, to_addr, subject, content, settings)

