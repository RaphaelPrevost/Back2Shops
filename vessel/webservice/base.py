import copy
import logging
import falcon
import time
import ujson
import settings
from datetime import datetime

from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils import db_utils
from B2SUtils.errors import DatabaseError
from B2SUtils.errors import ValidationError
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context


class BaseResource(object):
    request = None
    response = None
    conn = None

    encrypt = True
    service = SERVICES.USR

    def on_get(self, req, resp, **kwargs):
        self.request = req
        self.response = resp
        self._msg_handler('get', req, resp, **kwargs)

    def on_post(self, req, resp, **kwargs):
        self.request = req
        self.response = resp
        self._msg_handler('post', req, resp, **kwargs)

    def _msg_handler(self, method_name, req, resp, **kwargs):
        start_time = time.time() * 1000
        params = copy.copy(req._params)
        if params.get('password'):
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
        return {'res': RESP_RESULT.F,
                'err': 'INVALID_REQUEST'}

    def _on_post(self, req, resp, conn, **kwargs):
        return {'res': RESP_RESULT.F,
                'err': 'INVALID_REQUEST'}

    def gen_resp(self, resp, data):
        pass

    def encrypt_resp(self, resp, content):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
            content,
            settings.SERVER_APIKEY_URI_MAP[self.service],
            settings.PRIVATE_KEY_PATH)
        return resp

    def redirect(self, redirect_to):
        self.response.status = falcon.HTTP_302
        self.response.set_header('Location', redirect_to)


class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        if not self.encrypt:
            return gen_json_resp(resp, data)
        else:
            return self.encrypt_resp(resp, ujson.dumps(data))

    def encrypt_resp(self, resp, content):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
            content,
            settings.SERVER_APIKEY_URI_MAP[self.service],
            settings.PRIVATE_KEY_PATH)
        return resp
