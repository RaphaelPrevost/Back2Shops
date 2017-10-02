# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


import binascii
import hashlib
import hmac
import re
import weasyprint

from common.template import ENV

def _temp_content(template, **data):
    temp = ENV.get_template(template)
    content = temp.render(**data)
    return content

def _pdf_resp(resp, content):
    wp = weasyprint.HTML(string=content)
    pdf = wp.render().write_pdf()
    resp.body = pdf
    resp.content_type = "application/pdf"
    return resp

def _html_resp(resp, content):
    resp.body = content
    resp.content_type = "text/html"
    return resp

def gen_html_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _html_resp(resp, content)

def gen_pdf_resp(template, resp, **data):
    content = _temp_content(template, **data)
    return _pdf_resp(resp, content)

def gen_400_html_resp(resp):
    content = _temp_content('400.html')
    return _html_resp(resp, content)

def gen_400_pdf_resp(resp):
    content = _temp_content('400.html')
    return _pdf_resp(resp, content)

def gen_500_html_resp(resp):
    content = _temp_content('500.html')
    return _html_resp(resp, content)

def gen_500_pdf_resp(resp):
    content = _temp_content('500.html')
    return _pdf_resp(resp, content)

def gen_hmac(key, msg, algorithm=hashlib.sha512):
    return hmac.new(binascii.unhexlify(key), msg, algorithm).hexdigest()


def mask_cc_num(cc_num):
    return ('{}{:*>' + str(len(cc_num) - 8) + '}'
            ).format(cc_num[:4], cc_num[-4:])

def is_valid_cc_num(cc_num):
    return re.match(r'^\d{13,19}$', cc_num)

def is_valid_cvc(cvc):
    return re.match(r'^\d{3,4}$', cvc)

