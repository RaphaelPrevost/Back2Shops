import logging
import settings
import smtplib
from email.Message import Message
from email.Header import Header
from email.Utils import formatdate

from common.m17n import trans_func
from common.utils import gen_html_body
from common.utils import run_command

def send_email(to, subject, content):
    if not settings.SEND_EMAILS:
        return

    sender = settings.SERVICE_EMAIL
    message = _get_message(sender, to, subject, content)
    try:
        s = smtplib.SMTP()
        s.connect(settings.MAIL_HOST)
        s.starttls()
        s.login(settings.MAIL_FROM_USER, settings.MAIL_FROM_PASS)
        s.sendmail(sender, to, message)
        s.quit()
        return True
    except Exception, e:
        status, _ = run_command('sendmail %s' % to, input=message)
        if status == 0: return True

        logging.error("Failed to send email to: %s "
                      "with content: %s "
                      "for error: %s",
                      to, content, str(e),
                      exc_info=True)
        return False

def _get_message(_from, _to, _sub, _content):
    if isinstance(_sub, unicode):
        _sub = _sub.encode('UTF8')
    if isinstance(_content, unicode):
        _content = _content.encode('UTF8')
    message = Message()
    message['From'] = Header(_from, 'ascii')
    message['To'] = Header(_to, 'ascii')
    message['Subject'] = Header(_sub, 'UTF8')
    message['Mime-Version'] = '1.0'
    message['Date'] = formatdate(localtime=True)
    message['Content-Type'] = 'text/html; charset="UTF8"'
    message['Content-Transfer-Encoding'] = '8bit'
    message.set_payload(_content)
    return message.as_string()

def send_new_user_email(to_addr, data):
    subject = trans_func('NEW_USER_EMAIL_SUBJECT')
    content = gen_html_body('new_user_email.html', data, layout=None)
    send_email(to_addr, subject, content)

def send_order_email(to_addr, data):
    subject = trans_func('ORDER_EMAIL_SUBJECT')
    content = gen_html_body('order_email.html', data, layout=None)
    send_email(to_addr, subject, content)

