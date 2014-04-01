import unittest

from common.test_utils import is_backoffice_server_running
from tests.base_order_test import BaseOrderTestCase
from B2SUtils import db_utils

SKIP_REASON = "Please run backoffice server before running this test"

class TestInvoice(BaseOrderTestCase):
    ''' Shop address are configured to US - AL in backoffice
    for shop 1000002
    '''
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testDiffCountry(self):
        # update user address to China BJ
        self.b.update_account_address(self.users_id, "CN", "BJ", "BeiJing")

        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': 2,
            'id_shop': 1000002,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        # conf data in backtoshops
        type_attr_price = 3
        handling_fee = 6.0
        tax1 = 3
        tax2 = 4
        expect_amount = (type_attr_price*2.0 +
                         handling_fee +
                         type_attr_price*2.0 * tax1 / 100.0 +
                         type_attr_price*2.0 * tax2 / 100.0)

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)

        self.b.post_invoices(id_order)
        self.expect_one_item_result(id_order, expect_amount)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testDiffProvince(self):
        # update user address to US AK
        self.b.update_account_address(self.users_id,
                                      "US",
                                      "AK",
                                      "Alaska")

        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': 2,
            'id_shop': 1000002,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        # conf data in backoffice
        type_attr_price = 3
        handling_fee = 6.0
        tax1 = 1/100.0
        tax2 = 2/100.0
        expect_amount = (type_attr_price*2.0 +
                         handling_fee +
                         type_attr_price*2.0 * tax1 +
                         type_attr_price*2.0 * (1+tax1) * tax2)

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)

        self.b.post_invoices(id_order)
        self.expect_one_item_result(id_order, expect_amount)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testSameProvince(self):
        # update user address to US AK
        self.b.update_account_address(self.users_id,
                                      "US",
                                      "AL",
                                      "ALABAMA")

        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': 2,
            'id_shop': 1000002,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        # conf data in backoffice
        type_attr_price = 3
        handling_fee = 6.0
        tax1 = 1/100.0
        tax2 = 0.5/100.0
        tax3 = 1/100.0
        expect_amount = (type_attr_price*2.0 +
                         handling_fee +
                         type_attr_price*2.0 * tax1 +
                         type_attr_price*2.0 * tax2 +
                         handling_fee * tax3)

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone,
                                         self.shipaddr,
                                         self.billaddr,
                                         wwwOrder)

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
            self.assertEqual(amount_due,
                             exp_amount_due,
                             "amount_due %s is not same with expected: %s"
                             % (amount_due, exp_amount_due))
