import datetime

import settings
from common.test_utils import BaseTestCase
from common.test_utils import UsersBrowser
from common.utils import generate_random_str
from common.utils import gen_cookie_expiry
from common.utils import _parse_auth_cookie
from B2SUtils import db_utils

class TestUserAuth(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.email = "%s@example.com" % generate_random_str()
        self.password = generate_random_str()
        self.register()

    def test_login(self):
        self.login()

        # succeed
        self.pass_auth_verification()

        # failed: clear cookies
        self.b.clear_cookies()
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_UNSET_COOKIE")

    def test_bad_ip(self):
        auth_cookie = self.login()
        self.b.addheaders = [('x-forwarded-for', '127.0.1.1')]
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_USER")

    def test_bad_browser_headers(self):
        auth_cookie = self.login()
        self.b.addheaders = [('User-Agent', 'Windows IE 9')]
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_USER")

    def test_bad_csrf(self):
        auth_cookie = self.login()
        old_data = _parse_auth_cookie(auth_cookie.value.strip('"'))

        # csrf updated every request
        self.pass_auth_verification()
        new_auth_cookie = self.b.get_cookies().get(settings.USER_AUTH_COOKIE_NAME)
        new_data = _parse_auth_cookie(new_auth_cookie.value.strip('"'))
        self.assertNotEquals(old_data['csrf'], new_data['csrf'])

        # failed with old cookie
        self._make_auth_cookie(auth_cookie, old_data)
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_CSRF")

    def test_bad_cookie(self):
        auth_cookie = self.login()
        old_data = _parse_auth_cookie(auth_cookie.value.strip('"'))

        # bad csrf
        new_data = old_data.copy()
        new_data['csrf'] = generate_random_str(32)
        self._make_auth_cookie(auth_cookie, new_data)
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_HMAC")

        # bad auth
        new_data = old_data.copy()
        new_data['auth'] = generate_random_str(128)
        self._make_auth_cookie(auth_cookie, new_data)
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_HMAC")

        # bad expires
        new_data = old_data.copy()
        new_data['exp'] = gen_cookie_expiry(datetime.datetime.utcnow())
        self._make_auth_cookie(auth_cookie, new_data)
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_HMAC")

    def test_two_browsers(self):
        # login from browser a
        browser_a = UsersBrowser()
        browser_a.addheaders = [('User-Agent', 'Mac Mozilla')]
        self.login(browser_a)

        # login from browser b
        browser_b = UsersBrowser()
        browser_b.addheaders = [('User-Agent', 'Windows IE 9')]
        self.login(browser_b)

        # both works
        self.pass_auth_verification(browser_a)
        self.pass_auth_verification(browser_b)
        self.pass_auth_verification(browser_a)

    def test_expired_session(self):
        auth_cookie = self.login()
        data = _parse_auth_cookie(auth_cookie.value.strip('"'))

        with db_utils.get_conn() as conn:
            db_utils.update(conn, "users_logins",
                            {"cookie_expiry": datetime.datetime.utcnow()},
                            where={"users_id": data["users_id"]})
        self.fail_auth_verification("LOGIN_REQUIRED_ERR_INVALID_USER")

    def register(self, browser=None):
        return BaseTestCase.register(self, self.email, self.password,
                                     browser=browser)

    def login(self, browser=None):
        return BaseTestCase.login(self, self.email, self.password,
                                  browser=browser)

    def pass_auth_verification(self, browser=None):
        return BaseTestCase.pass_auth_verification(self, self.email,
                                                   browser=browser)

    def _make_auth_cookie(self, auth_cookie, new_data):
        auth_cookie.value = '"%s"' % '&'.join(['%s=%s' % (k, v)
                                        for k, v in new_data.iteritems()])
        self.b.set_cookies([auth_cookie])

