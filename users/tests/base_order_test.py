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


import ujson
from random import choice

from common.constants import ADDR_TYPE
from common.constants import GENDER
from common.test_utils import BaseTestCase
from common.test_utils import MockResponse
from common.test_utils import UsersBrowser
from common.utils import _parse_auth_cookie
from common.utils import generate_random_str
from common.utils import generate_random_digits_str
from B2SUtils import db_utils
from B2SRespUtils.generate import gen_xml_resp




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
        r = ujson.loads(r)
        self.assertTrue(r['res'] == 'SUCCESS', r)
        self.assertTrue(r['id'] > 0, r)
        return r['id']

    def success_wwwOrder(self, telephone, shipaddr, billaddr, wwwOrder):
        r = self.b.do_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)
        r = ujson.loads(r)
        self.assertTrue(r['res'] == 'SUCCESS', r)
        self.assertTrue(r['id'] > 0, r)
        return r['id']

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

    def _shipmentsCountCheck(self, id_order, expected_count):
        sql = """SELECT id
                   FROM shipments
                  WHERE id_order=%s
               ORDER BY id
         """
        with db_utils.get_conn() as conn:
            results = db_utils.query(conn, sql, (id_order,))
        shipments_index = [item[0] for item in results]
        self.assertEqual(len(shipments_index),
                         expected_count,
                         "Shipments count is not as expected:"
                         "%s-%s" % (shipments_index, expected_count))
        return shipments_index


class BaseShipmentTestCase(BaseOrderTestCase):
    def _freeShippingCheck(self, id_shipment, expecte_shipping_fee):
        sql = """SELECT fee
                   FROM free_shipping_fee
                  WHERE id_shipment =%s
         """
        with db_utils.get_conn() as conn:
            results = db_utils.query(conn, sql, (id_shipment,))
        self.assertTrue(len(results) > 0,
                        'No free shipping fee record '
                        'found for shipment: %s' % id_shipment)
        self.assertEqual(results[0][0],
                         expecte_shipping_fee,
                         'Free shipping fee for: %s is '
                         'not as expected: %s - %s'
                         % (id_shipment, results[0][0],
                            expecte_shipping_fee))

    def _shipping_list_item(self, id_shipment):
        sql = """SELECT id
                   FROM shipping_list
                  WHERE id_shipment=%s
         """
        with db_utils.get_conn() as conn:
            results = db_utils.query(conn, sql, (id_shipment,))
        return [item[0] for item in results]

    def _order_item(self, id_order):
        sql = """SELECT id_item
                   FROM order_details
                  WHERE id_order=%s
         """
        with db_utils.get_conn() as conn:
            results = db_utils.query(conn, sql, (id_order,))
        return [item[0] for item in results]


    def _successShipment(self, id_shipment,
                         expect_order=None, expect_status=None,
                         expect_shipping_fee=None,
                         expect_handling_fee=None,
                         expect_none_shipping_fee=False,
                         expect_none_handling_fee=False,
                         expect_supported_services=None):
        def __shipment_check():
            columns = ["id_order", "status"]
            sql = """SELECT %s
                       FROM shipments
                      WHERE id=%%s
             """ % ", ".join(columns)
            with db_utils.get_conn() as conn:
                results = db_utils.query(conn, sql,
                                         (id_shipment, ))
            self.assertTrue(len(results) > 0,
                            'Shipment-%s not exist' % id_shipment)

            r = dict(zip(tuple(columns), tuple(results[0])))
            if expect_order is not None:
                self.assertEqual(
                    r['id_order'],
                    expect_order,
                    'shipment(id_order) is not as expected: %s-%s'
                    % (r['id_order'], expect_order))

            if expect_status is not None:
                self.assertEqual(
                    r['status'],
                    expect_status,
                    'shipment(status) is not as expected: %s-%s'
                    % (r['status'], expect_status))

        def __shipping_fee_check():
            columns = ["id_shipment", "handling_fee", "shipping_fee"]
            sql = """SELECT %s
                       FROM shipping_fee
                      WHERE id_shipment=%%s
             """ % ", ".join(columns)
            with db_utils.get_conn() as conn:
                results = db_utils.query(conn, sql,
                                         (id_shipment, ))
            if (expect_handling_fee is not None or
                        expect_shipping_fee is not None):
                self.assert_(
                    len(results),
                    'There is no fee for shipment: %s'
                    % id_shipment)

            r = results and results[0] or None
            if expect_none_shipping_fee:
                self.assert_(
                    r is None or r['shipping_fee'] is None,
                    'shipment(shipping_fee) is not as expected: %s-%s'
                    % (r and r['shipping_fee'] or None, None))

            if expect_none_handling_fee:
                self.assert_(
                    r is None or r['shipping_fee'] is None,
                    'shipment(handling_fee) is not as expected: %s-%s'
                    % (r and r['handling_fee'] or None, None))


            if expect_shipping_fee is not None:
                self.assertEqual(
                    r['shipping_fee'],
                    expect_shipping_fee,
                    'shipment(shipping_fee) is not as expected: %s-%s'
                    % (r['shipping_fee'], expect_shipping_fee))

            if expect_handling_fee is not None:
                self.assertEqual(
                    r['handling_fee'],
                    expect_handling_fee,
                    'shipment(handling_fee) is not as expected: %s-%s'
                    % (r['handling_fee'], expect_handling_fee))

        def __support_services_check():
            if expect_supported_services is None:
                return
            columns = ["id_shipment", "id_postage", "supported_services"]
            sql = """SELECT %s
                       FROM shipping_supported_services
                      WHERE id_shipment=%%s
             """ % ", ".join(columns)
            with db_utils.get_conn() as conn:
                results = db_utils.query(conn, sql,
                                         (id_shipment, ))
            self.assert_(
                len(results),
                'There is no supported services for shipment: %s'
                % id_shipment)
            r = results[0]
            if expect_supported_services is not None:
                self.assertEqual(
                    r['supported_services'],
                    expect_supported_services,
                    'shipment(supported_services) is not as expected: %s-%s'
                    % (r['supported_services'], expect_supported_services))
        __shipment_check()
        __support_services_check()
        __shipping_fee_check()

    def _xml_resp_check(self, template, data, resp_content):
        mock_resp = MockResponse()
        expect_resp = gen_xml_resp(template, mock_resp, **data)

        self.assertEqual(expect_resp.body.strip(),
                         resp_content.strip(),
                         "Xml response is not as expected: \n"
                         "Resp: %s \n"
                         "Expected: %s" % (resp_content, expect_resp.body))
