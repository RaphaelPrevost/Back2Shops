import copy
import logging
import time
from datetime import datetime

from common import db_utils
from common.error import DatabaseError
from common.error import ValidationError
from common.utils import cookie_verify
from common.utils import gen_json_response
from common.constants import RESP_RESULT

class BaseResource:
    login_required = {'get': False, 'post': False}

    def on_get(self, req, resp, **kwargs):
        self._msg_handler('get', req, resp, **kwargs)

    def on_post(self, req, resp, **kwargs):
        self._msg_handler('post', req, resp, **kwargs)

    def _msg_handler(self, method_name, req, resp, **kwargs):
        start_time = time.time() * 1000
        params = req._params
        if params.get('password'):
            params = copy.copy(req._params)
            params['password'] = 'XXX'
        with db_utils.get_conn() as conn:
            try:
                logging.info('Got %s requet at %s UTC, %s with params %s'
                              % (req.method, datetime.utcnow(),
                                 req.uri, params))
                if self.login_required.get(method_name):
                    users_id = cookie_verify(conn, req, resp)
                    kwargs['users_id'] = users_id
                method = getattr(self, '_on_' + method_name)
                method(req, resp, conn, **kwargs)
            except ValidationError, e:
                gen_json_response(resp,
                         {'res': RESP_RESULT.F,
                          'err': str(e)})
            except DatabaseError, e:
                logging.error('Server DB Error: %s', (e,), exc_info=True)
                gen_json_response(resp,
                        {"res": RESP_RESULT.F,
                         "err": "DB_ERR",
                         "ERR_SQLDB": str(e)})
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                gen_json_response(resp,
                         {'res': RESP_RESULT.F,
                          'err': 'SERVER_ERR'})
        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, With: %s in %s ms'
                     % (req.method, req.uri, params,
                        resp.body, end_time - start_time))

    def _on_get(self, req, resp, conn, **kwargs):
        pass

    def _on_post(self, req, resp, conn, **kwargs):
        pass

