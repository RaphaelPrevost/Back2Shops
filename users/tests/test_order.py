import ujson
from random import choice
import settings

from common.constants import ADDR_TYPE
from common.constants import GENDER
from common.test_utils import BaseTestCase
from common.test_utils import UsersBrowser
from common.utils import generate_random_str
from common.utils import generate_random_digits_str
from common.utils import gen_cookie_expiry
from common.utils import _parse_auth_cookie
from B2SUtils import db_utils

class OrderBrowser(UsersBrowser):
    def do_posOrder(self, telephone, upc_shop, order):
        """ order format: [(barcode1, quantity1),
                           (barcode2, quantity2)]
        """
        o = [','.join([str(bc), str(qtt)]) for bc, qtt in order]
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
        addr = {
            'addr_type_0': ADDR_TYPE.Shipping,
            'address_0': generate_random_str(15),
            'city_0': 'Alabama',
            'postal_code_0': generate_random_digits_str(6),
            'country_code_0': 'US',
            'province_code_0': 'AL',
            'address_desp_0': 'test address',

            'addr_type_1': ADDR_TYPE.Billing,
            'address_1': generate_random_str(15),
            'city_1': 'Alabama',
            'postal_code_1': generate_random_digits_str(6),
            'country_code_1': 'US',
            'province_code_1': 'AL',
            'address_desp_1': 'test address'
        }
        account = {'action': 'modify',
                   'email': email}
        account.update(profile)
        account.update(phone)
        account.update(addr)

        resp = self._access("webservice/1.0/pub/account",
                            account)
        return resp.get_data(), account


class TestOrder(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.b = OrderBrowser()
        self.email = "%s@example.com" % generate_random_str()
        self.password = generate_random_str()
        self.register()

    def success_posOrder(self, telephone, upc_shop, posOrder):
        r = self.b.do_posOrder(telephone, upc_shop, posOrder)
        self.assertTrue(r.isdigit() and int(r) > 0, r)

    def success_wwwOrder(self, telephone, shipaddr, billaddr, wwwOrder):
        r = self.b.do_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)
        self.assertTrue(r.isdigit() and int(r) > 0, r)

    def testOrderInUniqueShop(self):
        auth_cookie = self.login()
        user = _parse_auth_cookie(auth_cookie.value.strip('"'))
        users_id = user['users_id']
        telephone, shipaddr, billaddr = self.get_user_info(users_id)

        # test posOrder items in unique shop.
        # order: shop:1
        #        barcode:11111, barcode:11112 for sale:1
        #        barcode:22221, barcode:22222 for sale:2
        upc_shop = '11111'
        posOrder = [('11111', 1),
                    ('11112', 2),
                    ('22221', 3),
                    ('22222', 4)]
        self.success_posOrder(telephone, upc_shop, posOrder)

        # test wwwOrder items in unique shop.
        # order:
        wwwOrder = [
            {'id_sale': 1, 'id_variant': 1, 'quantity': 5, 'id_shop': 1},
            {'id_sale': 1, 'id_variant': 2, 'quantity': 6, 'id_shop': 1},
            {'id_sale': 2, 'id_variant': 3, 'quantity': 7, 'id_shop': 1},
            {'id_sale': 2, 'id_variant': 4, 'quantity': 8, 'id_shop': 1}
        ]
        self.success_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)

    def testOrderInDiffShopSameBrand(self):
        auth_cookie = self.login()
        user = _parse_auth_cookie(auth_cookie.value.strip('"'))
        users_id = user['users_id']
        telephone, shipaddr, billaddr = self.get_user_info(users_id)

        # test posOrder items in shop 1, brand 1.
        # order: shop:1,
        #        barcode:11111, barcode:11112 for sale:1
        upc_shop = '11111'
        posOrder = [('11111', 1),
                    ('11112', 2)]
        self.success_posOrder(telephone, upc_shop, posOrder)

        # test posOrder items in shop 2, brand 1.
        #        shop:2,
        #        barcode:33331, barcode:33332 for sale:3
        upc_shop = '22222'
        posOrder = [('33331', 3),
                    ('33332', 4)]
        self.success_posOrder(telephone, upc_shop, posOrder)

        # test wwwOrder items in unique shop.
        # order:
        wwwOrder = [
            {'id_sale': 1, 'id_variant': 1, 'quantity': 5, 'id_shop': 1},
            {'id_sale': 1, 'id_variant': 2, 'quantity': 6, 'id_shop': 1},
            {'id_sale': 3, 'id_variant': 5, 'quantity': 7, 'id_shop': 2},
            {'id_sale': 3, 'id_variant': 6, 'quantity': 8, 'id_shop': 2}
        ]
        self.success_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)

    def testOrderInDiffShopDiffBrand(self):
        auth_cookie = self.login()
        user = _parse_auth_cookie(auth_cookie.value.strip('"'))
        users_id = user['users_id']
        telephone, shipaddr, billaddr = self.get_user_info(users_id)

        # test posOrder items in shop 1, brand 1.
        # order: shop:1,
        #        barcode:11111, barcode:11112 for sale:1
        upc_shop = '11111'
        posOrder = [('11111', 1),
                    ('11112', 2)]
        self.success_posOrder(telephone, upc_shop, posOrder)

        # test posOrder items in shop 3, brand 2.
        #        shop:3,
        #        barcode:44441, barcode:44442 for sale:4
        upc_shop = '33333'
        posOrder = [('44441', 3),
                    ('44442', 4)]
        self.success_posOrder(telephone, upc_shop, posOrder)

        # test wwwOrder items in unique shop.
        # order:
        wwwOrder = [
            {'id_sale': 1, 'id_variant': 1, 'quantity': 5, 'id_shop': 1},
            {'id_sale': 1, 'id_variant': 2, 'quantity': 6, 'id_shop': 1},
            {'id_sale': 4, 'id_variant': 7, 'quantity': 7, 'id_shop': 3},
            {'id_sale': 4, 'id_variant': 8, 'quantity': 8, 'id_shop': 3}
        ]
        self.success_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)

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

