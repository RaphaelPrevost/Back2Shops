import logging
import os
import unittest
import ujson
import urllib
from falcon.request import Request
from falcon.response import Response
from mechanize import Browser
from mechanize import Cookie

import settings
from B2SProtocol.constants import RESP_RESULT
from B2SProtocol.constants import USER_AUTH_COOKIE_NAME
from B2SUtils.db_utils import init_db_pool

class BaseBrowser(Browser):
    def get_cookies(self, host='localhost.local', path='/'):
        return self._ua_handlers['_cookies'].cookiejar._cookies[host][path]

    def clear_cookies(self):
        self._ua_handlers['_cookies'].cookiejar.clear()

    def set_cookies(self, cookies, domain='localhost.local', path='/'):
        """
        1. Set the cookies for this browser. The argument 'cookies' is better
        be a dict whose keys and values are strings like:
        browser.set_cookies({'key1': 'value2', 'key2': 'value2'})
        2. 'cookies' could also be a list of mechanize.Cookie objects.
        """
        if isinstance(cookies, tuple):
            cookies = list(cookies)
        if isinstance(cookies, dict):
            cookies = cookies.items()
        elif not isinstance(cookies, list):
            raise ValueError('argument cookies should be dict, list or tuple')
        cookie_objects = []
        for c in cookies:
            if isinstance(c, list) or isinstance(c, tuple):
                if len(c) != 2:
                    raise ValueError('too many elements, expected: 2')
                c = Cookie(version=0,
                           name=str(c[0]),
                           value=str(c[1]),
                           port=None,
                           port_specified=False,
                           domain=domain,
                           domain_specified=False,
                           domain_initial_dot=False,
                           path=path,
                           path_specified=False,
                           secure=False,
                           expires=None,
                           discard=True,
                           comment=None,
                           comment_url=None,
                           rest={})

            if isinstance(c, Cookie):
                cookie_objects.append(c)
            else:
                raise ValueError('cannot convert %s to a Cookie' % type(c))

        for cobj in cookie_objects:
            self._ua_handlers['_cookies'].cookiejar.set_cookie(cobj)


class UsersBrowser(BaseBrowser):
    def _access(self, path, post_data=None):
        url = "http://localhost:%s/%s" % (settings.SERVER_PORT, path)
        if post_data is not None:
            post_data = urllib.urlencode(post_data)
        logging.info("Browser access %s: %s" % (url, post_data))
        return self.open(url, post_data)

    def create_account(self, email, password):
        resp = self._access("webservice/1.0/pub/account",
                            {"action": "create",
                             "email": email,
                             "password": password})
        return resp.get_data()

    def login(self, email, password):
        resp = self._access("webservice/1.0/pub/connect",
                            {"email": email,
                             "password": password})
        return resp.get_data()

    def get_users_info(self):
        resp = self._access("webservice/1.0/pub/account")
        return resp.get_data()


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        init_db_pool(settings.DATABASE)
        self.b = UsersBrowser()

    def register(self, email, password, browser=None):
        if browser is None:
            browser = self.b
        resp = browser.create_account(email, password)
        self.assertEquals(ujson.loads(resp),
                         {"res": RESP_RESULT.S, "err": ""})

    def login(self, email, password, browser=None):
        if browser is None:
            browser = self.b
        resp = browser.login(email, password)
        self.assertEquals(ujson.loads(resp),
                         {"res": RESP_RESULT.S, "err": ""})
        cookie = browser.get_cookies()
        return cookie.get(USER_AUTH_COOKIE_NAME)

    def pass_auth_verification(self, email, browser=None):
        if browser is None:
            browser = self.b
        resp = ujson.loads(browser.get_users_info())
        self.assertTrue('email' in resp)
        self.assertTrue(resp['email']['value'], email)

    def fail_auth_verification(self, err, browser=None):
        if browser is None:
            browser = self.b
        resp = ujson.loads(browser.get_users_info())
        self.assertEquals(resp,
                         {"res": RESP_RESULT.F, "err": err})


class MockResponse(Response):
    pass


class MockRequest(Request):
    pass


def is_backoffice_server_running():
    if settings.PRODUCTION:
        return True

    if len( os.popen(
            "ps -aef | grep 'manage.py runserver' | grep -v 'grep' | awk '{ print $3 }'")\
        .read().strip().split( '\n' ) ) > 1:
        return True
    else:
        return False

def is_finace_server_running():
    pids = os.popen(
            "ps -aef | grep 'python fin_server.py' | grep -v 'grep' | awk '{ print $3 }'") \
            .read().strip().split( '\n' )
    pids = [pid for pid in pids if pid]
    if len(pids) == 1:
        return True
    else:
        return False
