import settings
import Cookie
import copy
import falcon
import logging
import re
import time
from datetime import datetime

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils.base_actor import as_list
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.constants import Redirection
from common.data_access import data_access
from common.m17n import trans_func
from common.utils import cur_symbol
from common.utils import format_amount
from common.utils import gen_html_resp
from common.utils import get_normalized_name
from common.utils import get_thumbnail
from common.utils import get_url_format


class BaseResource(object):
    login_required = {'get': False, 'post': False}
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
        logging.info('Got %s request at %s UTC, %s with params %s'
                     % (req.method, datetime.utcnow(),
                        req.uri, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        if data is not None:
            self.handle_cookies(resp, data)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, in %s ms'
                     % (req.method, req.uri, params,
                        end_time - start_time))

    def msg_handler(self, method_name, req, resp, **kwargs):
        try:
            self._verify_user_online(req, resp, method_name)
            method = getattr(self, '_on_' + method_name)
            data = method(req, resp, **kwargs)
        except Redirection, e:
            data = self.handle_redirection(e)
            if not data: return
        except ValidationError, e:
            logging.error('Validation Error: %s', (e,), exc_info=True)
            data = {'res': RESP_RESULT.F,
                    'err': str(e)}
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)
            data = {'res': RESP_RESULT.F,
                    'err': 'SERVER_ERR'}
        return data

    def _verify_user_online(self, req, resp, method_name):
        remote_resp = data_access(REMOTE_API_NAME.ONLINE,
                                  req, resp)
        if remote_resp.get('res') == RESP_RESULT.F:
            self.users_id = None
            if self.login_required.get(method_name):
                raise Redirection(self.get_auth_url(),
                                    err=remote_resp.get('err') or '')
        else:
            self.users_id = remote_resp['users_id']

    def get_auth_url(self):
        return get_url_format(FRT_ROUTE_ROLE.USER_AUTH)

    def handle_redirection(self, redirection):
        data = {'res': RESP_RESULT.F,
                'err': redirection.err,
                'redirect_to': redirection.redirect_to}
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
    base_template = settings.DEFAULT_TEMPLATE
    tabs = [
        {'name': 'E-shop', 'url': '/e-shop'},
        {'name': 'Lookbook', 'url': '/lookbook'},
    ]
    cur_tab_index = -1
    show_products_menu = True

    def __init__(self, **kwargs):
        super(BaseHtmlResource, self).__init__(**kwargs)
        self.route_args = kwargs

    def gen_resp(self, resp, data):
        try:
            if isinstance(data, dict):
                self._add_common_data(data)
                resp = gen_html_resp(self.template, resp, data,
                                     lang='en', layout=self.base_template)
            else:
                resp.body = data
                resp.content_type = "text/html"
            return resp
        except Exception, e:
            logging.error('Got error when rendering template(%s): %s',
                          self.template, e, exc_info=True)
            if self.request.path == '/error':
                raise
            else:
                self.redirect('/error')

    def handle_redirection(self, redirection):
        self.redirect(redirection.redirect_to)

    def get_single_attribute(self, data, key):
        resp = data.get(key, '')
        if isinstance(resp, list):
            resp = resp[0]
        return resp

    def _add_common_data(self, resp_dict):
        resp_dict['users_id'] = self.users_id
        resp_dict['tabs'] = copy.deepcopy(self.tabs)
        resp_dict['cur_tab_index'] = self.cur_tab_index
        if self.cur_tab_index >= 0:
            resp_dict['tabs'][self.cur_tab_index]['current'] = True
        if self.cur_tab_index != 0:
            self.show_products_menu = False
        resp_dict['show_products_menu'] = self.show_products_menu

        if self.show_products_menu:
            # navigation menu
            remote_resp = data_access(REMOTE_API_NAME.GET_TYPES,
                                      seller=settings.BRAND_ID)
            if remote_resp.get('res') == RESP_RESULT.F:
                resp_dict['err'] = remote_resp.get('err')
            else:
                resp_dict['menus'] = remote_resp
                for v in resp_dict['menus'].itervalues():
                    v['url_name'] = get_normalized_name(
                        FRT_ROUTE_ROLE.TYPE_LIST, 'type_name', v['name'])
            if 'cur_type_id' not in resp_dict:
                resp_dict['cur_type_id'] = -1

        if 'err' not in resp_dict:
            resp_dict['err'] = ''
        resp_dict['err'] = trans_func(resp_dict['err'])
        resp_dict['route_args'] = self.route_args

        resp_dict['as_list'] = as_list
        resp_dict['get_single_attribute'] = self.get_single_attribute
        resp_dict['format_amount'] = format_amount
        resp_dict['cur_symbol'] = cur_symbol
        resp_dict['get_thumbnail'] = get_thumbnail
        resp_dict.update({
            'prodlist_url_format': get_url_format(FRT_ROUTE_ROLE.PRDT_LIST),
            'auth_url_format': get_url_format(FRT_ROUTE_ROLE.USER_AUTH),
            'logout_url_format': get_url_format(FRT_ROUTE_ROLE.USER_LOGOUT),
            'user_url_format': get_url_format(FRT_ROUTE_ROLE.USER_INFO),
            'my_account_url_format': get_url_format(FRT_ROUTE_ROLE.MY_ACCOUNT),
            'basket_url_format': get_url_format(FRT_ROUTE_ROLE.BASKET),
            'order_auth_url_format': get_url_format(FRT_ROUTE_ROLE.ORDER_AUTH),
            'order_user_url_format': get_url_format(FRT_ROUTE_ROLE.ORDER_USER),
            'order_addr_url_format': get_url_format(FRT_ROUTE_ROLE.ORDER_ADDR),
            'order_info_url_format': get_url_format(FRT_ROUTE_ROLE.ORDER_INFO),
            'order_invoice_url_format': get_url_format(FRT_ROUTE_ROLE.ORDER_INVOICES),
            'order_list_url_format': get_url_format(FRT_ROUTE_ROLE.ORDER_LIST),
            'type_list_url_format': get_url_format(FRT_ROUTE_ROLE.TYPE_LIST),
        })

class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        if isinstance(data, dict) and 'err' in data:
            data['err'] = trans_func(data['err'])
        return gen_json_resp(resp, data)

