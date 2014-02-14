import copy
import logging
import time
import ujson
import settings
from datetime import datetime

from common.utils import cookie_verify
from common.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SRespUtils.generate import gen_xml_resp
from B2SRespUtils.generate import gen_text_resp
from B2SUtils import db_utils
from B2SUtils.errors import DatabaseError
from B2SUtils.errors import ValidationError
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context

class BaseResource(object):
    login_required = {'get': False, 'post': False}

    def on_get(self, req, resp, **kwargs):
        self.request = req
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
                        req.uri, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, With: %s in %s ms'
                     % (req.method, req.uri, params,
                        resp.body, end_time - start_time))

    def msg_handler(self, method_name, req, resp, **kwargs):
        with db_utils.get_conn() as conn:
            try:
                if self.login_required.get(method_name):
                    users_id = cookie_verify(conn, req, resp)
                    kwargs['users_id'] = users_id
                method = getattr(self, '_on_' + method_name)
                data = method(req, resp, conn, **kwargs)
            except ValidationError, e:
                data = {'res': RESP_RESULT.F,
                        'err': str(e)}
            except DatabaseError, e:
                logging.error('Server DB Error: %s', (e,), exc_info=True)
                data = {"res": RESP_RESULT.F,
                        "err": "DB_ERR",
                        "ERR_SQLDB": str(e)}
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                data = {'res': RESP_RESULT.F,
                        'err': 'SERVER_ERR'}
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
            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
            settings.PRIVATE_KEY_PATH)
        return resp

class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        return gen_json_resp(resp, data)

class BaseXmlResource(BaseResource):
    template = ""
    def gen_resp(self, resp, data):
        return gen_xml_resp(self.template, resp, **data)

class BaseTextResource(BaseResource):
    def gen_resp(self, resp, content):
        return gen_text_resp(resp, content)

class BaseEncryptJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        debugging = self.request._params.get('debugging') or ""
        if (settings.CRYPTO_RESP_DEBUGING and
            debugging.lower() == 'true'):
            gen_json_resp(resp, data)
        else:
            return self.encrypt_resp(resp, ujson.dumps(data))

class BaseEncryptXmlJsonResource(BaseEncryptJsonResource):
    template = ""
    def gen_resp(self, resp, data):
        resp = gen_xml_resp(self.template, resp, **data)
        debugging = self.request._params.get('debugging') or ""
        if (settings.CRYPTO_RESP_DEBUGING and
                    debugging.lower() == 'true'):
            return resp
        else:
            return self.encrypt_resp(resp, resp.body)
