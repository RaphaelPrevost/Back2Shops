import logging
import smtplib
import subprocess
from email.Message import Message
from email.Header import Header
from email.Utils import formatdate


def send_email(sender, to, subject, content, settings):
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


def run_command(cmd, input=None):
    """
    Returns a pair (return_code, output)
    Return (return_code, output) of executing cmd in a shell.
    """
    stdin = subprocess.PIPE if input else None
    p = subprocess.Popen('{ ' + cmd + '; } 2>&1',
                         shell=True, stdin=stdin, stdout=subprocess.PIPE)
    text, _ = p.communicate(input)
    return p.returncode, text.rstrip('\n')

