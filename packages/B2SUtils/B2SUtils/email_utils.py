# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


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

