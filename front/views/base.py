import copy
import falcon
import logging
import time
from datetime import datetime

import settings
from common.utils import gen_html_resp
from B2SProtocol.constants import RESP_RESULT
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
        for name in ('password', 'password2'):
            if params.get(name):
                params = copy.copy(req._params)
                params[name] = '******'
        logging.info('Got %s requet at %s UTC, %s with params %s'
                     % (req.method, datetime.utcnow(),
                        req.uri, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, in %s ms'
                     % (req.method, req.uri, params,
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

    def redirect(self, redirect_to):
        self.response.status = falcon.HTTP_302
        self.response.set_header('Location', redirect_to)


class BaseHtmlResource(BaseResource):
    template = ""

    def gen_resp(self, resp, data):
        self._add_common_data(data)

        if isinstance(data, dict):
            resp = gen_html_resp(self.template, resp, data)
        else:
            resp.body = data
            resp.content_type = "text/html"
        return resp

    def _add_common_data(self, resp_dict):
        if 'title' not in resp_dict:
            resp_dict['title'] = 'Dragon Dollar & Chinese Coins'
        if 'err' not in resp_dict:
            resp_dict['err'] = ''

