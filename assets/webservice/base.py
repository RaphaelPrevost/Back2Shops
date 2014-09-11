import falcon
import logging
import time
from datetime import datetime

from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils.errors import ValidationError


class BaseResource(object):
    request = None
    response = None

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
        params = req._params
        logging.info('Got %s requet at %s UTC, %s with params %s'
                     % (req.method, datetime.utcnow(),
                        req.path, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, in %s ms'
                     % (req.method, req.path, params,
                        end_time - start_time))

    def msg_handler(self, method_name, req, resp, **kwargs):
        try:
            method = getattr(self, '_on_' + method_name)
            data = method(req, resp, **kwargs)
        except ValidationError, e:
            logging.error('Validation Error: %s', (e,), exc_info=True)
            data = {'res': RESP_RESULT.F,
                    'err': str(e)}
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)
            data = {'res': RESP_RESULT.F,
                    'err': 'SERVER_ERR'}
        return data

    def _on_get(self, req, resp, **kwargs):
        return {}

    def _on_post(self, req, resp, **kwargs):
        return {}

    def gen_resp(self, resp, data):
        raise NotImplementedError


class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        return gen_json_resp(resp, data)

