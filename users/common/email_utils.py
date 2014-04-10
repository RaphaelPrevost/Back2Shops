import logging
import settings
import smtplib

from email.mime.text import MIMEText


def send_html_email(to, subject, content):
    if not isinstance(to, list):
        to = [to]

    me = (settings.MAIL_FROM_USER +
          "<" + settings.MAIL_FROM_USER
          + "@" +
          settings.MAIL_POSTFIX + ">")
    msg = MIMEText(content, _subtype='html')
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ";".join(to)
    try:
        s = smtplib.SMTP()
        s.connect(settings.MAIL_HOST)
        s.starttls()
        s.login(settings.MAIL_FROM_USER, settings.MAIL_FROM_PASS)
        s.sendmail(me, to, msg.as_string())
        s.quit()
        return True
    except Exception, e:
        logging.error("Failed to send email to: %s "
                      "with content: %s "
                      "for error: %s",
                      ";".join(to), content, str(e),
                      exc_info=True)
        return False
