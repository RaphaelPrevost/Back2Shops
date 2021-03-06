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


import settings
import Cookie
import copy
import falcon
import gevent
import logging
import re
import time
from datetime import datetime, timedelta

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import SESSION_COOKIE_NAME
from B2SProtocol.constants import EXPIRY_FORMAT

from B2SRespUtils.generate import gen_json_resp
from B2SUtils.base_actor import as_list
from B2SUtils.common import set_cookie, get_cookie
from B2SUtils.errors import ValidationError
from common.constants import FRT_ROUTE_ROLE
from common.constants import Redirection
from common.data_access import data_access
from common.utils import get_basket
from common.m17n import get_locale
from common.m17n import set_locale
from common.redis_utils import get_redis_cli
from common.utils import calc_before_tax_price
from common.utils import cur_symbol
from common.utils import format_amount
from common.utils import format_datetime
from common.utils import gen_html_resp
from common.utils import gen_cookie_expiry
from common.utils import gen_SID
from common.utils import get_err_msg
from common.utils import get_normalized_name
from common.utils import get_price_label
from common.utils import get_thumbnail
from common.utils import get_url_format
from common.utils import zero
from minify_css_files import get_loader_css
from minify_js_files import get_loader_js


class BaseResource(object):
    login_required = {'get': False, 'post': False}
    request = None
    response = None
    users_id = None

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
        params = copy.copy(req._params)
        for name in ('password', 'password2'):
            if params.get(name):
                params[name] = '******'
        logging.info('Got %s request at %s UTC, %s with params %s'
                     % (req.method, datetime.utcnow(),
                        req.path, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        if data is not None:
            self.handle_cookies(resp, data)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, in %s ms'
                     % (req.method, req.path, params,
                        end_time - start_time))

    def msg_handler(self, method_name, req, resp, **kwargs):
        try:
            #TODO set user locale
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
        finally:
            self.set_session(req, resp)
        return data

    def set_session(self, req, resp):
        def __gen_session_expiry():
            delta = timedelta(seconds=settings.SESSION_EXP_TIME)
            utc_expiry = datetime.utcnow() + delta
            return gen_cookie_expiry(utc_expiry)

        def __set(_sid):
            _exp = __gen_session_expiry()
            session = "sid@%s&exp@%s" % (_sid, _exp)

            set_cookie(resp,
                       SESSION_COOKIE_NAME,
                       session)

            name = 'SID:%s' % _sid
            cli = get_redis_cli(ping=True)
            if not cli: return
            cli.setex(name,
                      self.users_id or "",
                      settings.SESSION_EXP_TIME)

        def __set_session():
            sid = gen_SID()
            __set(sid)
            __remote_log(sid)

        def __up_session(_sid):
            cli = get_redis_cli(ping=True)
            if not cli: return
            name = 'SID:%s' % _sid
            if not cli.get(name) and self.users_id:
                __remote_log(_sid)
            __set(_sid)

        def __remote_log(_sid):
            values = {'sid': _sid}
            if self.users_id:
                values['users_id'] = self.users_id
            gevent.spawn(data_access, REMOTE_API_NAME.LOG_VISITORS,
                         req, resp, **values)

        cookie = get_cookie(req)
        session = cookie and cookie.get(SESSION_COOKIE_NAME)
        session = session and session.value.split('&')
        session = session and [tuple(field.split('@'))
                                     for field in session if field]
        try:
            session = session and dict(session)
            sid = session and session['sid'] or None
            exp = session and session['exp'] or None
        except Exception, e:
            sid = None
            exp = None

        if exp:
            expiry = datetime.strptime(exp, EXPIRY_FORMAT)
            if expiry > datetime.utcnow():
                __up_session(sid)
            else:
                __set_session()
        else:
            __set_session()

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
            # no cache for logged-in users
            resp.set_header('progma', 'no-cache')
            resp.set_header('cache-control', 'private, no-store, max-age=0, '
                       'no-cache, must-revalidate, post-check=0, pre-check=0')
            resp.set_header('expires', '0')

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
            cookie_header = resp._headers['set-cookie']
            cookie_header = re.sub(r'expires=(.*?);', r'expires="\1";', cookie_header)
            c = Cookie.SimpleCookie()
            c.load(cookie_header)
            for key in c:
                js_str = c[key].output().replace('"', '\\"')
                js_str = js_str.replace('Set-Cookie: ', '')
                js_str = 'document.cookie = "%s";' % js_str
                if js_str:
                    data['set_cookies_js'] += js_str

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
        {'name': 'La saga', 'url': '/la-saga'},
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
                                     lang=get_locale(),
                                     layout=self.base_template)
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

    def _add_basket_quantity(self):
        _, basket_data = get_basket(self.request, self.response)
        quantity = 0
        for _, qty in basket_data.iteritems():
            quantity += int(qty)
        return quantity

    def _add_common_data(self, resp_dict):
        resp_dict['users_id'] = self.users_id
        resp_dict['tabs'] = copy.deepcopy(self.tabs)
        resp_dict['cur_tab_index'] = self.cur_tab_index
        if self.cur_tab_index >= 0:
            resp_dict['tabs'][self.cur_tab_index]['current'] = True
        if self.cur_tab_index != 0:
            self.show_products_menu = False
        resp_dict['show_products_menu'] = self.show_products_menu
        resp_dict['css_loader'] = get_loader_css(settings.BRAND_NAME.lower())
        resp_dict['js_loader'] = get_loader_js(settings.BRAND_NAME.lower())
        resp_dict['js_defer_loader'] = get_loader_js(settings.BRAND_NAME.lower(), True)

        if self.show_products_menu:
            # navigation menu
            remote_resp = data_access(REMOTE_API_NAME.GET_TYPES,
                                      seller=settings.BRAND_ID)
            if remote_resp.get('res') == RESP_RESULT.F:
                resp_dict['err'] = remote_resp.get('err')
            else:
                resp_dict['menus'] = remote_resp.values()
                for v in resp_dict['menus']:
                    v['url_name'] = get_normalized_name(
                        FRT_ROUTE_ROLE.TYPE_LIST, 'type_name', v['name'])
                resp_dict['menus'].sort(cmp=
                    lambda x, y: cmp(int(x.get('sort_order') or 0),
                                     int(y.get('sort_order') or 0)))
            if 'cur_type_id' not in resp_dict:
                resp_dict['cur_type_id'] = -1

        if 'err' not in resp_dict:
            resp_dict['err'] = ''
        resp_dict['err'] = get_err_msg(resp_dict['err'])
        resp_dict['route_args'] = self.route_args

        need_calc_before_tax = calc_before_tax_price(self.request,
                                                     self.response)
        resp_dict['calc_before_tax_price'] = need_calc_before_tax
        resp_dict['price_label'] = get_price_label(need_calc_before_tax)

        resp_dict['format_datetime'] = format_datetime
        resp_dict['as_list'] = as_list
        resp_dict['get_single_attribute'] = self.get_single_attribute
        resp_dict['format_amount'] = format_amount
        resp_dict['zero'] = zero
        resp_dict['cur_symbol'] = cur_symbol
        resp_dict['get_thumbnail'] = get_thumbnail
        resp_dict['basket_qty'] = self._add_basket_quantity()
        resp_dict.update({
            'prodlist_url_format': get_url_format(FRT_ROUTE_ROLE.PRDT_LIST),
            'auth_url_format': get_url_format(FRT_ROUTE_ROLE.USER_AUTH),
            'logout_url_format': get_url_format(FRT_ROUTE_ROLE.USER_LOGOUT),
            'reset_pwd_req_url_format': get_url_format(FRT_ROUTE_ROLE.RESET_PWD_REQ),
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
            data['err'] = get_err_msg(data['err'])
        return gen_json_resp(resp, data)

