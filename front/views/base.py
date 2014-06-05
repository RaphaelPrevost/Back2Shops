import Cookie
import copy
import falcon
import logging
import re
import time
from datetime import datetime

import settings
from common.constants import FRT_ROUTE_ROLE
from common.data_access import data_access
from common.utils import gen_html_resp
from common.utils import get_url_format
from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils.errors import ValidationError


class BaseResource(object):
    request = None
    response = None

    def __init__(self, **kwargs):
        object.__init__(self)

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
        self.handle_cookies(resp, data)
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

    def handle_cookies(self, resp, data):
        data['set_cookies_js'] = ''
        if 'set-cookie' in resp._headers:
            c = Cookie.SimpleCookie()
            c.load(resp._headers['set-cookie'])
            m = re.findall(r'(document\.cookie.*\n)', c.js_output())
            if m:
                data['set_cookies_js'] = ''.join(m)

    def _on_get(self, req, resp, **kwargs):
        return {}

    def _on_post(self, req, resp, **kwargs):
        return {}

    def gen_resp(self, resp, data):
        raise NotImplementedError

    def redirect(self, redirect_to, code=falcon.HTTP_302):
        self.response.status = code
        self.response.location = redirect_to


class BaseHtmlResource(BaseResource):
    template = ""

    def __init__(self, **kwargs):
        super(BaseHtmlResource, self).__init__(**kwargs)
        self.title = kwargs.get('title') or ''
        self.desc = kwargs.get('desc') or ''

    def gen_resp(self, resp, data):
        if isinstance(data, dict):
            self._add_common_data(data)
            resp = gen_html_resp(self.template, resp, data, lang='en')
        else:
            resp.body = data
            resp.content_type = "text/html"
        return resp

    def get_single_attribute(self, data, key):
        resp = data.get(key, '')
        if(isinstance(resp, list)):
            resp = resp[0]

        return resp

    def _add_common_data(self, resp_dict):
        resp_dict['get_single_attribute'] = self.get_single_attribute

        # navigation menu
        remote_resp = data_access(REMOTE_API_NAME.GET_TYPES,
                                  seller=settings.BRAND_ID)
        if remote_resp.get('res') == RESP_RESULT.F:
            resp_dict['err'] = remote_resp.get('err')
        else:
            resp_dict['menus'] = remote_resp

        if 'err' not in resp_dict:
            resp_dict['err'] = ''
        resp_dict['title'] = self.title
        resp_dict['desc'] = self.desc

        resp_dict.update({
            'prodlist_url_format': get_url_format(FRT_ROUTE_ROLE.PRDT_LIST),
            'basket_url_format': get_url_format(FRT_ROUTE_ROLE.BASKET),
        })

class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        return gen_json_resp(resp, data)
