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


import copy
import logging
import time
import ujson
import settings
from datetime import datetime

from common.constants import RESP_RESULT
from B2SRespUtils.generate import gen_html_resp
from B2SRespUtils.generate import gen_json_resp
from B2SRespUtils.generate import gen_pdf_resp
from B2SRespUtils.generate import gen_xml_resp
from B2SRespUtils.generate import gen_text_resp
from B2SUtils import db_utils
from B2SUtils.errors import DatabaseError
from B2SUtils.errors import ValidationError
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context

class BaseResource(object):
    encrypt = False
    request = None
    response = None
    conn = None
    service = SERVICES.ADM

    def on_get(self, req, resp, **kwargs):
        self.request = req
        self.response = resp
        self._msg_handler('get', req, resp, **kwargs)

    def on_post(self, req, resp, **kwargs):
        self.request = req
        self._msg_handler('post', req, resp, **kwargs)

    def _msg_handler(self, method_name, req, resp, **kwargs):
        start_time = time.time() * 1000
        params = req._params
        if params.get('password'):
            params = copy.copy(req._params)
            params['password'] = '******'
        logging.info('Got %s requet at %s UTC, %s with params %s'
                     % (req.method, datetime.utcnow(),
                        req.path, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, With: %s in %s ms'
                     % (req.method, req.path, params,
                        resp.body, end_time - start_time))

    def msg_handler(self, method_name, req, resp, **kwargs):
        with db_utils.get_conn() as conn:
            self.conn = conn
            try:
                method = getattr(self, '_on_' + method_name)
                data = method(req, resp, conn, **kwargs)
            except ValidationError, e:
                logging.error('Validation Error: %s', (e,), exc_info=True)
                data = {'res': RESP_RESULT.F,
                        'err': str(e)}
                conn.rollback()
            except DatabaseError, e:
                logging.error('Server DB Error: %s', (e,), exc_info=True)
                data = {"res": RESP_RESULT.F,
                        "err": "DB_ERR",
                        "ERR_SQLDB": str(e)}
                conn.rollback()
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                data = {'res': RESP_RESULT.F,
                        'err': 'SERVER_ERR'}
                conn.rollback()
        return data

    def _on_get(self, req, resp, conn, **kwargs):
        pass

    def _on_post(self, req, resp, conn, **kwargs):
        pass

    def gen_resp(self, resp, data):
        pass

    def encrypt_resp(self, resp, content):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
            content,
            settings.SERVER_APIKEY_URI_MAP[self.service],
            settings.PRIVATE_KEY_PATH)
        return resp

    def debugging_resp(self):
        debugging = self.request._params.get('debugging') or ""
        if (settings.CRYPTO_RESP_DEBUGING and
            debugging.lower() == 'true'):
            return True
        return False

class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        if not self.encrypt or self.debugging_resp():
            return gen_json_resp(resp, data)
        else:
            return self.encrypt_resp(resp, ujson.dumps(data))

class BaseTextResource(BaseResource):
    def gen_resp(self, resp, content):
        return gen_text_resp(resp, content)

class BaseXmlResource(BaseResource):
    template = ""
    def gen_resp(self, resp, data):
        if isinstance(data, dict):
            if 'error' in data or 'err' in data:
                data['error'] = data.get('error') or data.get('err')
                resp = gen_xml_resp('error.xml', resp, **data)
            else:
                resp = gen_xml_resp(self.template, resp, **data)
        else:
            resp.body = data
            resp.content_type = "application/xml"
        if not self.encrypt or self.debugging_resp():
            return resp
        else:
            return self.encrypt_resp(resp, resp.body)

class BaseHtmlResource(BaseResource):
    template = ""

    def gen_resp(self, resp, data):
        if isinstance(data, dict):
            if data.get('error') or data.get('err'):
                data['error'] = data.get('error') or data.get('err')
                resp = gen_html_resp('error.html', resp, **data)
            else:
                resp = gen_html_resp(self.template, resp, **data)
        else:
            resp.body = data
            resp.content_type = "text/html"

        if not self.encrypt or self.debugging_resp():
            return resp
        else:
            return self.encrypt_resp(resp, resp.body)

class BasePdfResource(BaseResource):
    template = ""
    def gen_resp(self, resp, data):
        if isinstance(data, dict):
            resp = gen_pdf_resp(self.template, resp, **data)
        else:
            resp.body = data
            resp.content_type = "application/pdf"

        if not self.encrypt or self.debugging_resp():
            return resp
        else:
            return self.encrypt_resp(resp, resp.body)
