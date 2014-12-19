# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


import unittest
import ujson

from common.test_utils import is_backoffice_server_running
from tests.base_order_test import BaseOrderTestCase
from B2SUtils import db_utils
from B2SUtils.common import to_round

SKIP_REASON = "Please run backoffice server before running this test"

class TestInvoice(BaseOrderTestCase):
    ''' Shop address are configured to US - AL in backoffice
    for shop 1000002
    '''
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testDiffCountry(self):

        # update user address to China BJ
        self.b.update_account_address(self.users_id, "CN", "BJ", "BeiJing")

        qty = 2
        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': qty,
            'id_shop': 1000002,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        # conf data in backtoshops
        type_attr_price = 3 * (1 + 0.02) # + premium
        weight = 2
        shipping_fee = 2.0 * weight * qty
        handling_fee = 6.0
        tax1 = 3/100.0
        tax2 = 4/100.0
        expect_amount = (
            type_attr_price*qty +
            handling_fee +
            shipping_fee +
            (to_round(type_attr_price * (1 + tax1)) - type_attr_price) * qty +
            (to_round(type_attr_price * (1 + tax2)) - type_attr_price) * qty)

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)
        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        self._shipping_conf(id_shp)

        self.b.post_invoices(id_order)
        self.expect_one_item_result(id_order, expect_amount)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testDiffProvince(self):
        # update user address to US AK
        self.b.update_account_address(self.users_id,
                                      "US",
                                      "AK",
                                      "Alaska")

        qty = 2
        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': qty,
            'id_shop': 1000002,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        # conf data in backoffice
        type_attr_price = 3 * (1 + 0.02) # + premium
        weight = 2
        shipping_fee = 2.0 * weight * qty
        handling_fee = 6.0
        tax1 = 1/100.0
        tax2 = 2/100.0

        t1_amount = (to_round(type_attr_price * (1 + tax1)) - type_attr_price) * qty
        after_amount = to_round(type_attr_price * (1 + tax1))
        t2_amount = (to_round(after_amount * (1 + tax2)) - after_amount) * qty
        expect_amount = (
            type_attr_price*qty +
            handling_fee +
            shipping_fee +
            t1_amount +
            t2_amount)

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)

        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        self._shipping_conf(id_shp)

        self.b.post_invoices(id_order)
        self.expect_one_item_result(id_order, expect_amount)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testSameProvince(self):
        # update user address to US AK
        self.b.update_account_address(self.users_id,
                                      "US",
                                      "AL",
                                      "ALABAMA")

        qty = 2
        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': qty,
            'id_shop': 1000002,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        # conf data in backoffice
        type_attr_price = 3 * (1 + 0.02) # + premium
        weight = 2
        shipping_fee = 2.0 * weight * qty
        handling_fee = 6.0
        tax1 = 1/100.0
        tax2 = 0.5/100.0
        tax3 = 1/100.0 # taxable
        expect_amount = (
            type_attr_price*qty +
            handling_fee +
            shipping_fee +
            (to_round(type_attr_price * (1 + tax1)) - type_attr_price) * qty +
            (to_round(type_attr_price * (1 + tax2)) - type_attr_price) * qty +
            (to_round(type_attr_price * (1 + tax3)) - type_attr_price) * qty +
            to_round((handling_fee + shipping_fee) * (1 + tax3)) - (handling_fee + shipping_fee))

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)
        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        self._shipping_conf(id_shp)

        self.b.post_invoices(id_order)
        self.expect_one_item_result(id_order, expect_amount)

    def expect_one_item_result(self, id_order, exp_amount_due):
        sql = """SELECT amount_due
                   FROM invoices
                  WHERE id_order = %s
        """
        with db_utils.get_conn() as conn:
            amount_due = db_utils.query(conn, sql, (id_order,))
            self.assertEqual(
                len(amount_due), 1,
                "There should have one invoice record for order %s" % id_order)
            amount_due = amount_due[0][0]
            self.assertAlmostEqual(float(amount_due),
                             float(exp_amount_due),
                             msg="order(%s) amount_due %s is not same with expected: %s"
                             % (id_order, amount_due, exp_amount_due))

    def _shipping_conf(self, id_shipment=None):
        id_carrier = 1
        id_service = 1
        params = {
            'shipment': id_shipment,
            'carrier': id_carrier,
            'service': id_service
        }
        url = "webservice/1.0/pub/shipping/conf"
        resp = self.b._access(url, params)
        return ujson.loads(resp.get_data())
