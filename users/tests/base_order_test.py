import ujson
from random import choice

from common.constants import ADDR_TYPE
from common.constants import GENDER
from common.test_utils import BaseTestCase
from common.test_utils import UsersBrowser
from common.utils import _parse_auth_cookie
from common.utils import generate_random_str
from common.utils import generate_random_digits_str
from B2SUtils import db_utils



SKIP_REASON = "Please run backoffice server before running this test"

class OrderBrowser(UsersBrowser):
    def do_posOrder(self, telephone, upc_shop, order):
        """ order format: [(barcode1, quantity1),
                           (barcode2, quantity2)]
        """
        o = [','.join([str(bc), str(qtt), str(tp)]) for bc, qtt, tp in order]
        o = '\\r\\n'.join(o)
        resp = self._access("webservice/1.0/pub/order",
                            {'action': 'create',
                             'telephone': telephone,
                             'upc_shop': upc_shop,
                             'posOrder': o})
        return resp.get_data()

    def do_wwwOrder(self, telephone, shipaddr, billaddr, order):
        """ order format:
            [
                {'id_sale': xxx,
                 'id_variant': xxx,
                 'quantity': xxx,
                 'id_shop': xxx},
                {'id_sale': xxx,
                 'id_variant': xxx,
                 'quantity': xxx,
                 'id_shop': xxx}
            ]
        """
        resp = self._access("webservice/1.0/pub/order",
                            {'action': 'create',
                             'telephone': telephone,
                             'shipaddr': shipaddr,
                             'billaddr': billaddr,
                             'wwwOrder': ujson.dumps(order)})
        return resp.get_data()

    def post_invoices(self, id_order):
        resp = self._access("webservice/1.0/pub/invoice/request",
                            {'order': id_order})
        return resp.get_data()

    def update_account(self, email):
        # profile info
        title_choices = ['Mr', 'Mrs', 'Miss', 'Ms']
        gender_choices = GENDER.toDict().values()
        profile = {
            'last_name': generate_random_str(5),
            'first_name': generate_random_str(3),
            'title': choice(title_choices),
            'gender': choice(gender_choices),
            'birthday': '1984-12-08',
            'locale': 'en-US'
        }

        # phone info
        phone = {
            'country_num_0': 'US',
            'phone_num_0': generate_random_digits_str(length=11),
            'phone_num_desp_0': 'test phone number',
            }

        # address info
        ship_addr = {
            'addr_type_0': ADDR_TYPE.Shipping,
            'address_0': generate_random_str(15),
            'city_0': 'Alabama',
            'postal_code_0': generate_random_digits_str(6),
            'country_code_0': 'US',
            'province_code_0': 'AL',
            'address_desp_0': 'test address',
        }
        bill_addr = {
            'addr_type_0': ADDR_TYPE.Billing,
            'address_0': generate_random_str(15),
            'city_0': 'Alabama',
            'postal_code_0': generate_random_digits_str(6),
            'country_code_0': 'US',
            'province_code_0': 'AL',
            'address_desp_0': 'test address'
        }
        account = {'action': 'modify',
                   'email': email}
        account.update(profile)
        account.update(phone)
        account.update(ship_addr)

        resp = self._access("webservice/1.0/pub/account",
                            account)

        account = {'action': 'modify',
                   'email': email}
        account.update(profile)
        account.update(phone)
        account.update(bill_addr)
        resp = self._access("webservice/1.0/pub/account",
                            account)
        return resp.get_data(), account

    def update_account_address(self, id_user, country, province, city):
        with db_utils.get_conn() as conn:
            db_utils.update(
                conn,
                "users_address",
                values={"country_code": country,
                        "province_code": province,
                        "city": city},
                where={'users_id': id_user})

class BaseOrderTestCase(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.b = OrderBrowser()
        self.login_with_new_user()

    def success_posOrder(self, telephone, upc_shop, posOrder):
        r = self.b.do_posOrder(telephone, upc_shop, posOrder)
        self.assertTrue(r.isdigit() and int(r) > 0, r)
        return int(r)

    def success_wwwOrder(self, telephone, shipaddr, billaddr, wwwOrder):
        r = self.b.do_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)
        self.assertTrue(r.isdigit() and int(r) > 0, r)
        return int(r)

    def get_user_info(self, users_id):
        browser = self.b
        browser.update_account(self.email)
        phone_id = self.get_telephone_id(users_id)[0][0]
        addrs = self.get_addr_id(users_id)
        shipaddr = 0
        billaddr = 0
        for addr_id, addr_type in addrs:
            if addr_type == ADDR_TYPE.Billing:
                billaddr = addr_id
            else:
                shipaddr = addr_id
        return phone_id, shipaddr, billaddr

    def get_telephone_id(self, users_id):
        sql = """SELECT id
                   FROM users_phone_num
                  WHERE users_id = %s
        """
        with db_utils.get_conn() as conn:
            phone_id = db_utils.query(conn, sql, (users_id,))
        return phone_id

    def get_addr_id(self, users_id):
        sql = """SELECT id, addr_type
                   FROM users_address
                  WHERE users_id = %s
        """
        with db_utils.get_conn() as conn:
            addrs = db_utils.query(conn, sql, (users_id,))
        return addrs

    def register(self, browser=None):
        return BaseTestCase.register(self, self.email, self.password,
                                     browser=browser)

    def login(self, browser=None):
        return BaseTestCase.login(self, self.email, self.password,
                                  browser=browser)


    def login_with_new_user(self):
        self.b.clear_cookies()
        self.email = "%s@example.com" % generate_random_str()
        self.password = generate_random_str()
        self.register()

        auth_cookie = self.login()
        user = _parse_auth_cookie(auth_cookie.value.strip('"'))
        self.users_id = user['users_id']
        (self.telephone, self.shipaddr,
         self.billaddr) = self.get_user_info(self.users_id)
