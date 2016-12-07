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


import datetime
import unittest
import ujson
import urllib

from common.error import ErrorCode as E_C
from common.test_utils import is_backoffice_server_running
from tests.base_order_test import BaseShipmentTestCase

from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SUCCESS
from B2SProtocol.constants import FAILURE
from B2SProtocol.settings import SHIPPING_CURRENCY
from B2SUtils import db_utils

SKIP_REASON = "Please run backoffice server before running this test"



class TestShipment(BaseShipmentTestCase):
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
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item1_handling_fee = 12.0
        item1_shipping_fee = 1.05*2
        carrier_shipping_item2 = {
            'id_sale': 1000007,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item2_handling_fee = 23.0
        item2_shipping_fee = 2.0*2
        invoice_shipping_item3 = {
            'id_sale': 1000008,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        flat_rate_shipping_item4 = {
            'id_sale': 1000009,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item4_handling_fee = 21.0
        item4_shipping_fee = 15.0
        free_shipping_item5 = {
            'id_sale': 1000010,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item5_fake_fee = 9.0 * 2
        custom_shipping_item6 = {
            'id_sale': 1000011,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item6_handling_fee = 23.0
        item6_shipping_fee = 5.0

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
                              expect_handling_fee=item4_handling_fee,
                              expect_shipping_fee=item4_shipping_fee)
        self._successShipment(id_spm_invoice,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_none_handling_fee=True,
                              expect_none_shipping_fee=True)
        expect_handling_fee = max([item1_handling_fee, item2_handling_fee])
        expect_shipping_fee = (item1_shipping_fee +
                               item2_shipping_fee)
        services = '{"1":"1"}'
        self._successShipment(id_spm_carrier,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_handling_fee=expect_handling_fee,
                              expect_shipping_fee=expect_shipping_fee,
                              expect_supported_services=services)
        services = '{"1000001":"0"}'
        self._successShipment(id_spm_custom,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_handling_fee=item6_handling_fee,
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
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item2_in_shop6 = {
            'id_sale': 1000028,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
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
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}

        item2_for_corporate4 = {
            'id_sale': 1000013,
            'id_variant': 0,
            'quantity': 1,
            'id_shop': 0,
            'id_type': 0,
            'id_price_type': 0,
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
        item1_quantity = 3
        item1_with_ems_usps = {
            'id_sale': 1000014,
            'id_variant': 0,
            'quantity': item1_quantity,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item1_handling_fee = 11.0
        item1_weight = 1.0

        item2_quantity = 2
        item2_with_ems_usps = {
            'id_sale': 1000015,
            'id_variant': 0,
            'quantity': item2_quantity,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item2_weight = 2.0
        item2_handling_fee = 12.0

        item3_quantity = 2
        item3_with_usps = {
            'id_sale': 1000016,
            'id_variant': 0,
            'quantity': item3_quantity,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item3_weight = 3.0
        item3_handling_fee = 13.0

        item4_quantity = 2
        item4_with_ems = {
            'id_sale': 1000017,
            'id_variant': 0,
            'quantity': item4_quantity,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item4_weight = 4.0
        item4_handling_fee = 14.0

        wwwOrder = [item1_with_ems_usps, item2_with_ems_usps,
                    item3_with_usps, item4_with_ems]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        spm1, spm2 = self._shipmentsCountCheck(id_order, 2)


        expect_handling_fee = max([item1_handling_fee,
                    item2_handling_fee,
                    item4_handling_fee])
        expect_shipping_fee =  2.0 * (item1_weight * item1_quantity +
                                      item2_weight * item2_quantity +
                                      item4_weight * item4_quantity)
        services = '{"1":"1"}'
        self._successShipment(spm1,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_handling_fee=expect_handling_fee,
                              expect_shipping_fee=expect_shipping_fee,
                              expect_supported_services=services)

        expect_handling_fee = item3_handling_fee
        expect_shipping_fee = 3.0 * item3_weight * item3_quantity
        services = '{"2":"2"}'
        self._successShipment(spm2,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_handling_fee=expect_handling_fee,
                              expect_shipping_fee=expect_shipping_fee,
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
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item1_handling_fee = 17.0

        item2_with_custom1_custom2 = {
            'id_sale': 1000019,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item2_handling_fee = 18.0

        item3_with_custom1 = {
            'id_sale': 1000020,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item3_handling_fee = 19.0

        item4_with_custom2 = {
            'id_sale': 1000021,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item4_handling_fee = 20.0

        custom1_fee = 5.0
        custom2_fee = 6.0

        wwwOrder = [item1_with_custom1_custom2, item2_with_custom1_custom2,
                    item3_with_custom1, item4_with_custom2]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        spm1, spm2 = self._shipmentsCountCheck(id_order, 2)
        expect_handling_fee = max(item1_handling_fee,
                   item2_handling_fee,
                   item3_handling_fee)
        services = '{"1000001":"0"}'
        self._successShipment(spm1,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_handling_fee=expect_handling_fee,
                              expect_shipping_fee=custom1_fee,
                              expect_supported_services=services)

        services = '{"1000002":"0"}'
        self._successShipment(spm2,
                              expect_order=id_order,
                              expect_status=SHIPMENT_STATUS.PACKING,
                              expect_handling_fee=item4_handling_fee,
                              expect_shipping_fee=custom2_fee,
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
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}

        item2_with_flat_rate = {
            'id_sale': 1000023,
            'id_variant': 0,
            'quantity': 3,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}

        item3_with_carrier_shipping = {
            'id_sale': 1000024,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}

        item4_with_custom_shipping = {
            'id_sale': 1000025,
            'id_variant': 0,
            'quantity': 3,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}

        item5_with_invoice_shipping = {
            'id_sale': 1000026,
            'id_variant': 0,
            'quantity': 2,
            'id_shop': 1000006,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}

        wwwOrder = [item1_with_free_shipping,
                    item2_with_flat_rate,
                    item3_with_carrier_shipping,
                    item4_with_custom_shipping,
                    item5_with_invoice_shipping]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        self._shipmentsCountCheck(id_order, 12)


class TestShippingList(BaseShipmentTestCase):
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test(self):
        item_with_carrier_shipping = {
            'id_sale': 1000029,
            'id_variant': 1000011,
            'quantity': 2,
            'id_shop': 1000002,
            'id_type': 1000003,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        wwwOrder = [item_with_carrier_shipping]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        self._reqInvoice(id_order)

        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        resp_content = self._shippingList(id_order)
        id_order_item = self._order_item(id_order)[0]
        id_spl_item = self._shipping_list_item(id_shp)[0]
        shipping_data = {
            'object_list': [
                {'carriers': [
                    {'id': u'1',
                     'name': u'EMS',
                     'services': [
                         {'desc': u'EMS express service',
                          'id': u'1',
                          'name': u'Express'}]
                    }],
                 'fee_info': {'handling_fee': 5.0,
                              'id': 349,
                              'id_shipment': 427L,
                              'shipping_fee': 6.0},
                 'id': 431,
                 'calculation_method': 3,
                 'id_brand': 1000001,
                 'id_shop': 1000002,
                 'tracking_name': None,
                 'shipping_carrier': 1,
                 'shipping_list': [
                     {'id_shipping_list': id_spl_item,
                      'id_item': id_order_item,
                      'shipping_status': 1,
                      'id_sale': 1000029L,
                      'id_variant': 1000011L,
                      'id_weight_type': 1000003L,
                      'quantity': 2,
                      'sale_item': {
                          'id': u'1000029',
                          'name': u'item1 type weight type price with variant',
                          'currency': 'EUR',
                          'quantity': 2,
                          'packing_quantity': 2,
                          'remaining_quantity': 0,
                          'sel_variant': {
                              'id': u'1000011',
                              'name': u'product brand attr for test',
                              'premium': {'text': u'1.0', 'type': u'ratio'},
                              'thumb': None},
                          'sel_weight_type': {
                              'id': u'1000003',
                              'name': u'common attr1 for product type 1',
                              'weight': u'1.5'},
                          'type': {
                              'id': u'1000001',
                              'name': u'product type 1'},
                          'weight': u'3.0',
                          'weight_unit': u'kg'}}],
                 'status': 1,
                 'postage': 1,
                 'tracking_info': None}],
            'shipping_currency': 'EUR',
            'shipping_weight_unit': 'kg',
            'order_create_date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'order_status': 2}
        shipping_data['object_list'][0]['id'] = id_shp
        self._xml_resp_check('shipping_list.xml',
                            shipping_data,
                            resp_content)

    def _shippingList(self, id_order):
        params = urllib.urlencode({'id_order': id_order})
        url = "webservice/1.0/pub/shipping/list?%s" % params
        resp = self.b._access(url)
        return resp.get_data()

    def _reqInvoice(self, id_order):
        url = "webservice/1.0/pub/invoice/request"
        resp = self.b._access(url, {'order': id_order})
        return resp.get_data()


class TestShippingFee(BaseShipmentTestCase):
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testShipmentShippingFee(self):
        item = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': 2,
            'id_shop': 1000002,
            'id_type': 1000003,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}

        wwwOrder = [item]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        id_carrier1 = 1
        id_carrier2 = 2
        id_service1 = 1
        id_service2 = 2

        exp_fee_1 = {
            'pk': id_carrier1,
            'name': 'EMS',
            'carrier_services': [
                {'pk': id_service1,
                 'name': 'Express',
                 'desc': 'EMS express service',
                 'shipping_fee': 8}]
        }

        exp_fee_2 = {
            'pk': id_carrier2,
            'name': 'USPS',
            'carrier_services': [
                {'pk': id_service2,
                 'name': 'Express',
                 'desc': 'USPS express service',
                 'shipping_fee': 12}]
        }

        # test shipping fee for shipment without specify service
        resp_content = self._shipping_fee({'shipment': id_shp})
        exp = {'carrier_rules': [exp_fee_1, exp_fee_2],
               'default_currency': SHIPPING_CURRENCY}

        self._xml_resp_check('shipping_fees_test.xml',
                             exp,
                             resp_content)

        # test shipping fee for shipment with specify service
        resp_content = self._shipping_fee({'shipment': id_shp,
                                           'carrier': id_carrier1,
                                           'service': id_service1})
        exp = {'carrier_rules': [exp_fee_1],
               'default_currency': SHIPPING_CURRENCY}

        self._xml_resp_check('shipping_fees_test.xml',
                             exp,
                             resp_content)

        # test shipping fee for shipment with not supported service
        resp_content = self._shipping_fee({'shipment': id_shp,
                                           'carrier': id_carrier1,
                                           'service': id_service1 + 10})
        exp = {'error': E_C.SPSF_NOT_SUPPORT_SERVICE[0]}

        self._xml_resp_check('error.xml',
                             exp,
                             resp_content)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testSaleShippingFee(self):
        id_sale = 1000031
        id_weight_type = 1000003

        id_carrier1 = 1
        id_carrier2 = 2
        id_service1 = 1
        id_service2 = 2

        exp_fee_1 = {
            'pk': id_carrier1,
            'name': 'EMS',
            'carrier_services': [
                {'pk': id_service1,
                 'name': 'Express',
                 'desc': 'EMS express service',
                 'shipping_fee': 4}]
        }

        exp_fee_2 = {
            'pk': id_carrier2,
            'name': 'USPS',
            'carrier_services': [
                {'pk': id_service2,
                 'name': 'Express',
                 'desc': 'USPS express service',
                 'shipping_fee': 6}]
        }

        # test shipping fee for sale without specify service
        resp_content = self._shipping_fee({'sale': id_sale,
                                           'weight_type': id_weight_type,
                                           'shop': 1000002})
        exp = {'carrier_rules': [exp_fee_1, exp_fee_2],
               'default_currency': SHIPPING_CURRENCY}

        self._xml_resp_check('shipping_fees_test.xml',
                             exp,
                             resp_content)

        # test shipping fee for sale with specify service
        resp_content = self._shipping_fee({'sale': id_sale,
                                           'weight_type': id_weight_type,
                                           'shop': 1000002,
                                           'carrier': id_carrier1,
                                           'service': id_service1})
        exp = {'carrier_rules': [exp_fee_1],
               'default_currency': SHIPPING_CURRENCY}

        self._xml_resp_check('shipping_fees_test.xml',
                             exp,
                             resp_content)

        # test shipping fee for sale with not supported service
        resp_content = self._shipping_fee({'sale': id_sale,
                                           'weight_type': id_weight_type,
                                           'shop': 1000002,
                                           'carrier': id_carrier1,
                                           'service': id_service1 + 10})
        exp = {'error': E_C.SSF_NOT_SUPPORT_SERVICE[0]}

        self._xml_resp_check('error.xml',
                             exp,
                             resp_content)

    def _shipping_fee(self, params):
        params = urllib.urlencode(params)
        url = "webservice/1.0/pub/shipping/fees?%s" % params
        resp = self.b._access(url)
        return resp.get_data()

class TestShippingConf(BaseShipmentTestCase):
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test(self):
        item1_with_2_services = {
            'id_sale': 1000031,
            'id_variant': 1000012,
            'quantity': 2,
            'id_shop': 1000002,
            'id_type': 1000003,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}
        item1_weight = 2.0
        item1_fee = item1_weight * 2 * 2

        item2_free_shipping = {
            'id_sale': 1000032,
            'id_variant': 1000013,
            'quantity': 1,
            'id_shop': 1000002,
            'id_type': 0,
            'id_price_type': 0,
            'id_weight_type': 0}
        item2_weight = 3.3
        item2_fake_fee = item2_weight * 2

        item3_with_1_service = {
            'id_sale': 1000033,
            'id_variant': 1000014,
            'quantity': 2,
            'id_shop': 1000002,
            'id_type': 1000003,
            'id_price_type': 1000003,
            'id_weight_type': 1000003}
        item3_weight = 3
        item3_fee = item3_weight * 2 * 2

        id_carrier1 = 1
        id_service1 = 1

        # test conf service for shipment which support 2 services
        wwwOrder = [item1_with_2_services]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        r = self._shipping_conf(id_shipment=id_shp,
                                id_carrier=id_carrier1,
                                id_service=id_service1)
        self._success_check(id_shp, r,
                            exp_postage=id_service1,
                            exp_fee=item1_fee)

        # test conf service for shipment which support 1 service
        # and grouped with free item
        wwwOrder = [item3_with_1_service, item2_free_shipping]
        id_order = self.success_wwwOrder(self.telephone, self.shipaddr,
                                         self.billaddr, wwwOrder)
        id_shp = self._shipmentsCountCheck(id_order, 1)[0]
        r = self._shipping_conf(id_shipment=id_shp,
                                id_carrier=id_carrier1,
                                id_service=id_service1)
        self._success_check(id_shp, r,
                            exp_postage=id_service1,
                            exp_fee=item3_fee,
                            exp_free_fee=item2_fake_fee)

        # failure test conf service with wrong service id
        r = self._shipping_conf(id_shipment=id_shp,
                                id_carrier=id_carrier1,
                                id_service=id_service1 + 10)
        self.assertEqual(r[FAILURE], E_C.SP_INVALID_SERVICE[0])

        # failure test access others shipment
        self.login_with_new_user()
        r = self._shipping_conf(id_shipment=id_shp,
                                id_carrier=id_carrier1,
                                id_service=id_service1)
        self.assertEqual(r[FAILURE], E_C.SP_PRIORITY_ERROR[0])

    def _success_check(self, id_shipment, resp_content, exp_postage=None,
                       exp_fee=None, exp_free_fee=None):
        self.assertEqual(resp_content, SUCCESS)

        conn = db_utils.get_conn()
        if exp_postage is not None:
            query_str = ("SELECT id_postage "
                           "FROM shipping_supported_services "
                          "WHERE id_shipment=%s")
            r = db_utils.query(conn, query_str, (id_shipment,))

            self.assert_(len(r),
                         "No supported service record for shipment: %s"
                         % id_shipment)
            self.assertEqual(int(r[0][0]), int(exp_postage))

        if exp_fee is not None:
            query_str = ("SELECT shipping_fee "
                           "FROM shipping_fee "
                          "WHERE id_shipment=%s")
            r = db_utils.query(conn, query_str, (id_shipment,))

            self.assert_(len(r),
                         "No shipping fee record for shipment: %s"
                         % id_shipment)
            self.assertEqual(float(r[0][0]), float(exp_fee))

        if exp_free_fee is not None:
            query_str = ("SELECT fee "
                           "FROM free_shipping_fee "
                          "WHERE id_shipment=%s")
            r = db_utils.query(conn, query_str, (id_shipment,))

            self.assert_(len(r),
                         "No free shipping fee record for shipment: %s"
                         % id_shipment)
            self.assertEqual(float(r[0][0]), float(exp_free_fee))

    def _shipping_conf(self, id_shipment=None,
                       id_carrier=None, id_service=None):
        params = {
            'shipment': id_shipment,
            'carrier': id_carrier,
            'service': id_service
        }
        url = "webservice/1.0/pub/shipping/conf"
        resp = self.b._access(url, params)
        return ujson.loads(resp.get_data())
