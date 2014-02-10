import ujson
import unittest

from common.constants import SHIPMENT_STATUS
from common.test_utils import is_backoffice_server_running
from common.utils import _parse_auth_cookie
from tests.base_order_test import BaseOrderTestCase
from B2SUtils import db_utils

SKIP_REASON = "Please run backoffice server before running this test"

class TestShipment(BaseOrderTestCase):
    def setUp(self):
        BaseOrderTestCase.setUp(self)
        auth_cookie = self.login()
        user = _parse_auth_cookie(auth_cookie.value.strip('"'))
        users_id = user['users_id']
        (self.telephone, self.shipaddr,
         self.billaddr) = self.get_user_info(users_id)

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

    def _successShipment(self, id_shipment,
                         expect_order=None, expect_status=None,
                         expect_shipping_fee=None,
                         expect_none_shipping_fee=False,
                         expect_supported_services=None):
        columns = ["id_order", "status", "shipping_fee",
                   "supported_services"]
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

        if expect_shipping_fee is not None:
            self.assertEqual(
                r['shipping_fee'],
                expect_shipping_fee,
                'shipment(shipping_fee) is not as expected: %s-%s'
                % (r['shipping_fee'], expect_shipping_fee))

        if expect_none_shipping_fee:
            self.assertEqual(
                r['shipping_fee'],
                None,
                'shipment(shipping_fee) is not as expected: %s-%s'
                % (r['shipping_fee'], None))

        if expect_supported_services is not None:
            self.assertEqual(
                r['supported_services'],
                expect_supported_services,
                'shipment(supported_services) is not as expected: %s-%s'
                % (r['supported_services'], expect_supported_services))

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testShipmentGroupInOneShop(self):
        """ Test case:
        target market: all items in shop 1000006
        Sale Items:
           * two items with automatic carrier shipping fees
           * one item with invoice shipping fees
           * one item with flat rate
           * one item with free shipping
           * one item with a custom computation
        Expect result:
           * 5 shipments
           * invoice shipping fee without a price.
        """
        carrier_shipping_item1 = {
            'id_sale': 1000006,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item1_shipping_fee = 12.0 + 1.05*2
        carrier_shipping_item2 ={
            'id_sale': 1000007,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item2_shipping_fee = 23.0 + 2.0*2
        invoice_shipping_item3 = {
            'id_sale': 1000008,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        flat_rate_shipping_item4 = {
            'id_sale': 1000009,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item4_shipping_fee = 21.0 + 15.0
        free_shipping_item5 = {
            'id_sale': 1000010,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item5_fake_fee = 9.0 * 2
        custom_shipping_item6 = {
            'id_sale': 1000011,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item6_shipping_fee = 23.0 + 5.0

        # order:
        wwwOrder = [carrier_shipping_item1,
                    carrier_shipping_item2,
                    invoice_shipping_item3,
                    flat_rate_shipping_item4,
                    free_shipping_item5,
                    custom_shipping_item6]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        shipment_index = self._shipmentsCountCheck(id_order, 4)
        (id_spm_flat_rate, id_spm_invoice, id_spm_carrier,
         id_spm_custom) = shipment_index
        self._successShipment(id_spm_flat_rate,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=item4_shipping_fee)
        self._successShipment(id_spm_invoice,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_none_shipping_fee=True)
        expect_shipping_fee = (item1_shipping_fee +
                               item2_shipping_fee -
                               12)
        services = '{"1":"1"}'
        self._successShipment(id_spm_carrier,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=expect_shipping_fee,
                              expect_supported_services=services)
        services = '{"1000001":"0"}'
        self._successShipment(id_spm_custom,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=item6_shipping_fee,
                              expect_supported_services=services)
        self._freeShippingCheck(id_spm_carrier, item5_fake_fee)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testShipmentGroupInDiffShop(self):
        """ Test Case:
        target market:
          * one item in shop5
          * one item in shop6
        sale items:
          * item1 - shop5, allow group, support EMS-Express, quantity 2
          * item1 - shop6, allow group, support EMS-Express, quantity 2
        expected result:
          * 2 shipments created

        """
        item1_in_shop5 = {
            'id_sale': 1000027,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000005,
            'id_weight_type': 0}
        item2_in_shop6 ={
            'id_sale': 1000028,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_weight_type': 0}
        wwwOrder = [item1_in_shop5,
                    item2_in_shop6]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        self._shipmentsCountCheck(id_order, 2)


    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testGroupByDiffCorporate(self):
        """ Test Case:
        target market: 2 internet sale items.
        sale items:
          * item for corporate 3 with carrier EMS service
          * item for corporate 4 with carrier EMS service
        expected result:
          * 2 shipments created

        """
        item1_for_corporate3 = {
            'id_sale': 1000012,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 0,
            'id_weight_type': 0}

        item2_for_corporate4 = {
            'id_sale': 1000013,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 0,
            'id_weight_type': 0}

        wwwOrder = [item1_for_corporate3, item2_for_corporate4]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        shipment_index = self._shipmentsCountCheck(id_order, 2)

        services = '{"1":"1"}'
        for id_shipment in shipment_index:
            self._successShipment(id_shipment,
                                  expect_order=id_order,
                                  expect_status=SHIPMENT_STATUS.PACKING,
                                  expect_supported_services=services)


    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testGroupByMostCommonCarrierService(self):
        """ Test Case:
        target market:  all items in shop 1000006
        sale items:
          * item1 supports EMS-Express, USPS-Express, quantity 2
          * item2 supports EMS-Express, USPS-Express, quantity 3
          * item3 supports USPS-Express, quantity 2
          * item4 supports EMS-Express, quantity 2
        Expect result:
          * shipment1: groups item1, item2, item4
          * shipment2: groups item3
        """
        item1_with_ems_usps = {
            'id_sale': 1000014,
            'id_variant': 0,
            'quantity': 3,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item1_handling_fee = 11.0
        item1_weight = 1.0

        item2_with_ems_usps = {
            'id_sale': 1000015,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item2_weight = 2.0
        item2_handling_fee = 12.0

        item3_with_usps = {
            'id_sale': 1000016,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item3_weight = 3.0
        item3_handling_fee = 13.0

        item4_with_ems = {
            'id_sale': 1000017,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item4_weight = 4.0
        item4_handling_fee = 14.0

        wwwOrder = [item1_with_ems_usps, item2_with_ems_usps,
                    item3_with_usps, item4_with_ems]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        spm1, spm2 = self._shipmentsCountCheck(id_order, 2)


        fee = (max([item1_handling_fee,
                    item2_handling_fee,
                    item4_handling_fee]) +
               2.0 * (item1_weight + item2_weight + item4_weight))
        services = '{"1":"1"}'
        self._successShipment(spm1,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=fee,
                              expect_supported_services=services)

        fee = item3_handling_fee + 3.0 * item3_weight
        services = '{"2":"2"}'
        self._successShipment(spm2,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=fee,
                              expect_supported_services=services)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testGroupByMostCommonCustomService(self):
        """ Test Case:
        target market:  all items in shop 1000006
        sale items:
          * item1 supports custom shipping 1, custom shipping2, quantity 2
          * item2 supports custom shipping 1, custom shipping2, quantity 3
          * item3 supports custom shipping 1, quantity 2
          * item4 supports custom shipping 2, quantity 2
        Expect result:
          * shipment1: groups item1, item2, item3
          * shipment2: groups item4
        """
        item1_with_custom1_custom2 = {
            'id_sale': 1000018,
            'id_variant': 0,
            'quantity': 3,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item1_handling_fee = 17.0

        item2_with_custom1_custom2 = {
            'id_sale': 1000019,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item2_handling_fee = 18.0

        item3_with_custom1 = {
            'id_sale': 1000020,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item3_handling_fee = 19.0

        item4_with_custom2 = {
            'id_sale': 1000021,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}
        item4_handling_fee = 20.0

        custom1_fee = 5.0
        custom2_fee = 6.0

        wwwOrder = [item1_with_custom1_custom2, item2_with_custom1_custom2,
                    item3_with_custom1, item4_with_custom2]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        spm1, spm2 = self._shipmentsCountCheck(id_order, 2)
        fee = (max(item1_handling_fee,
                   item2_handling_fee,
                   item3_handling_fee) +
               custom1_fee)
        services = '{"1000001":"0"}'
        self._successShipment(spm1,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=fee,
                              expect_supported_services=services)

        services = '{"1000002":"0"}'
        fee = item4_handling_fee + custom2_fee
        self._successShipment(spm2,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_shipping_fee=fee,
                              expect_supported_services=services)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testNotAllowGroups(self):
        """ Test Case:
        target market:  all items in shop 1000006
        sale items:
          * item1 - free shipping, quantity 2
          * item2 - flat rate, quantity 3
          * item3 - carrier shipping rate, quantity 2
          * item4 - custom shipping rate, quantity 3
          * item5 - invoice shipping, quantity 2
        Expect result:
          * 12 shipments create.
        """
        item1_with_free_shipping = {
            'id_sale': 1000022,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}

        item2_with_flat_rate = {
            'id_sale': 1000023,
            'id_variant': 0,
            'quantity': 3,
            'id_shop': 1000006,
            'id_weight_type': 0}

        item3_with_carrier_shipping = {
            'id_sale': 1000024,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}

        item4_with_custom_shipping = {
            'id_sale': 1000025,
            'id_variant': 0,
            'quantity': 3,
            'id_shop': 1000006,
            'id_weight_type': 0}

        item5_with_invoice_shipping = {
            'id_sale': 1000026,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_weight_type': 0}

        wwwOrder = [item1_with_free_shipping,
                    item2_with_flat_rate,
                    item3_with_carrier_shipping,
                    item4_with_custom_shipping,
                    item5_with_invoice_shipping]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        self._shipmentsCountCheck(id_order, 12)
