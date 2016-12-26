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
import unittest
import urllib
import xmltodict
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta

from B2SUtils import db_utils
from B2SUtils.base_actor import as_list
from common.test_utils import is_backoffice_server_running
from models.order import get_order_items
from tests.base_order_test import BaseOrderTestCase


SKIP_REASON = "Please start backoffice server before running this test"

class TestCouponOrder(BaseOrderTestCase):
    def setUp(self):
        super(TestCouponOrder, self).setUp()
        self.id_brand = 1000005
        self.bo_user = 1000006
        self.coupons = []

    def tearDown(self):
        for id_coupon in self.coupons:
            # delete coupon
            self._post_coupon({
                'action': 'delete',
                'id_coupon': id_coupon,
            })
        super(TestCouponOrder, self).tearDown()

    def _post_coupon(self, values):
        values.update({
            'id_issuer': self.id_brand,
            'debugging': 'true',
        })
        resp = self.b._access("webservice/1.0/private/coupon", values)
        data = xmltodict.parse(resp.get_data())
        id_coupon = data.get('coupons', {}).get('coupon', {}).get('@id')
        self.assert_(isinstance(id_coupon, basestring) and id_coupon.isdigit())
        if values['action'] == 'create':
            self.coupons.append(id_coupon)
        return id_coupon

    def _check_order_item(self, item, sale_id, name, quantity=1, price=None):
        self.assertEquals(item['sale_id'], sale_id)
        self.assertEquals(item['name'], name)
        self.assertEquals(item['quantity'], quantity)
        if price is not None:
            self.assertAlmostEqual(item['price'], price)

    def _check_invoice_item(self, item, name, price, taxes,
                            quantity=1, promo=False, free=False):
        self.assertEquals(item['name'].encode('utf8'), name)
        self.assertEquals(int(item['qty']), 1)
        self.assertAlmostEqual(float(item['price']['#text']), price)
        self.assertEquals(len(as_list(item['tax'])), len(taxes))
        for tax, expected_tax in zip(as_list(item['tax']), taxes):
            self.assertEquals(tax['@name'].encode('utf8'), expected_tax['name'])
            self.assertAlmostEqual(float(tax['@rate']), expected_tax['rate'])
            self.assertAlmostEqual(float(tax['#text']), expected_tax['tax'])
        self.assertEquals(item['promo'], str(promo))
        self.assertEquals(item['free'], str(free))

    def _get_invoice_items(self, id_order):
        invoice_xml = self.b.post_invoices(id_order)
        items = []
        for invoice_data in as_list(xmltodict.parse(invoice_xml)['invoices']['invoice']):
            items += as_list(invoice_data['item'])
        return items

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test_group_for_match_all(self):
        # The Dawanglu shop defines a promotion group: (三文鱼贝果+南瓜汤)
        # If a customer buys the holiday menu (both the bagel and the soup),
        # they get a free 菠萝包 and 鸳鸯咖啡.
        promotion_group = 1000001
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_GIVEAWAY',
            'require': ujson.dumps({
                "invoice_match": {
                    "promotion_group": [promotion_group],
                    "operation": "MATCH_ALL",
                },
            }),
            'gift': ujson.dumps([{"id": 1000037, "quantity":1},
                                 {"id": 1000039, "quantity":1}]),
        }
        self._post_coupon(coupon_values)

        # If a customer orders a bagel and a soup at the Qianmen shop,
        # they don't get any free item.
        wwwOrder = [
            {'id_sale': 1000034,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000035,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 2)
            self._check_order_item(all_order_items[0], 1000034, '三文鱼贝果')
            self._check_order_item(all_order_items[1], 1000035, '南瓜汤')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 2)
            self._check_invoice_item(invoice_items[0], '三文鱼贝果', 30,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 3},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.55},
                                     ])
            self._check_invoice_item(invoice_items[1], '南瓜汤', 26,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 2.6},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.21},
                                     ])

        # If a customer orders a bagel and a soup at Dawanglu,
        # they get the cafe and 菠萝包 for free.
        wwwOrder = [
            {'id_sale': 1000034,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000035,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 4)
            self._check_order_item(all_order_items[0], 1000034, '三文鱼贝果')
            self._check_order_item(all_order_items[1], 1000035, '南瓜汤')
            self._check_order_item(all_order_items[2], 1000037, '菠萝包')
            self._check_order_item(all_order_items[3], 1000039, '鸳鸯咖啡')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 4)
            self._check_invoice_item(invoice_items[0], '三文鱼贝果', 30,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 3},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.55},
                                     ])
            self._check_invoice_item(invoice_items[1], '南瓜汤', 26,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 2.6},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.21},
                                     ])
            self._check_invoice_item(invoice_items[2], '菠萝包', 0,
                                    [{'name': 'test local tax',
                                      'rate': 8.5, 'tax': 0.68},
                                     ], free=True, promo=True)
            self._check_invoice_item(invoice_items[3], '鸳鸯咖啡', 0,
                                    [{'name': 'test local tax',
                                      'rate': 8.5, 'tax': 1.36},
                                     ], free=True, promo=True)

        # If a customer orders only a soup, they don't get any free item.
        wwwOrder = [
            {'id_sale': 1000035,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 1)
            self._check_order_item(all_order_items[0], 1000035, '南瓜汤')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 1)
            self._check_invoice_item(invoice_items[0], '南瓜汤', 26,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 2.6},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.21},
                                     ])

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test_group_for_match_any(self):
        # The Dawanglu and Qianmen shops both define a promotion group
        # for hot drinks (奶茶, 鸳鸯咖啡).
        # If a customer orders ANY hot drinks, he gets a free 菠萝包.
        promotion_groups = [1000003, 1000004]
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_GIVEAWAY',
            'require': ujson.dumps({
                "invoice_match": {
                    "promotion_group": promotion_groups,
                },
            }),
            'gift': ujson.dumps([{"id": 1000037, "quantity":1}]),
        }
        self._post_coupon(coupon_values)

        # If a customer orders a 奶茶 at Qianmen, they get the free gifts
        wwwOrder = [
            {'id_sale': 1000038,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0}
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 2)
            self._check_order_item(all_order_items[0], 1000038, '奶茶')
            self._check_order_item(all_order_items[1], 1000037, '菠萝包')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 2)
            self._check_invoice_item(invoice_items[0], '奶茶', 14,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 1.4},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 1.19},
                                     ])
            self._check_invoice_item(invoice_items[1], '菠萝包', 0,
                                    [{'name': 'test local tax',
                                      'rate': 8.5, 'tax': 0.68},
                                     ], free=True, promo=True)

        # If a customer orders a 咖啡 at Dawanglu, they get the free gifts
        wwwOrder = [
            {'id_sale': 1000039,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0}
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 2)
            self._check_order_item(all_order_items[0], 1000039, '鸳鸯咖啡')
            self._check_order_item(all_order_items[1], 1000037, '菠萝包')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 2)
            self._check_invoice_item(invoice_items[0], '鸳鸯咖啡', 16,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 1.6},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 1.36},
                                     ])
            self._check_invoice_item(invoice_items[1], '菠萝包', 0,
                                    [{'name': 'test local tax',
                                      'rate': 8.5, 'tax': 0.68},
                                     ], free=True, promo=True)

        # If a customer orders a 苹果汁 at Qianmen, they don't get any gift
        wwwOrder = [
            {'id_sale': 1000040,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0}
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 1)
            self._check_order_item(all_order_items[0], 1000040, '苹果汁')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 1)
            self._check_invoice_item(invoice_items[0], '苹果汁', 12,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 1.2},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 1.02},
                                     ])

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test_sum_price(self):
        # The Qianmen shop has a special promotion: if a customer orders for
        # more than 50 yuan, they get a free coffee.
        id_shop = 1000008
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_GIVEAWAY',
            'require': ujson.dumps({
                "invoice_match": {
                    "shop": [id_shop],
                    "operation": "SUM_PRICE",
                    "more_than": 50,
                    "equal": 50,
                },
            }),
            'gift': ujson.dumps([{"id": 1000039, "quantity":1}]),
        }
        self._post_coupon(coupon_values)

        # If a customer orders a 三文鱼贝果 and a 南瓜汤 at Qianmen,
        # they get a free coffee.
        wwwOrder = [
            {'id_sale': 1000034,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': id_shop,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000035,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': id_shop,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 3)
            self._check_order_item(all_order_items[0], 1000034, '三文鱼贝果')
            self._check_order_item(all_order_items[1], 1000035, '南瓜汤')
            self._check_order_item(all_order_items[2], 1000039, '鸳鸯咖啡')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 3)
            self._check_invoice_item(invoice_items[0], '三文鱼贝果', 30,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 3},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.55},
                                     ])
            self._check_invoice_item(invoice_items[1], '南瓜汤', 26,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 2.6},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.21},
                                     ])
            self._check_invoice_item(invoice_items[2], '鸳鸯咖啡', 0,
                                    [{'name': 'test local tax',
                                      'rate': 8.5, 'tax': 1.36},
                                     ], promo=True, free=True)

        # If a customer orders only a 南瓜汤 at Qianmen,
        # they don't get any gift.
        wwwOrder = [
            {'id_sale': 1000035,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': id_shop,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 1)
            self._check_order_item(all_order_items[0], 1000035, '南瓜汤')

            invoice_items = self._get_invoice_items(id_order)
            self.assertEquals(len(invoice_items), 1)
            self._check_invoice_item(invoice_items[0], '南瓜汤', 26,
                                    [{'name': 'test general tax',
                                      'rate': 10, 'tax': 2.6},
                                     {'name': 'test local tax',
                                      'rate': 8.5, 'tax': 2.21},
                                     ])

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def test_discount_coupons(self):
        # Coupon A give a -20% on hot drinks (奶茶, 鸳鸯咖啡),
        # but expired !
        yesterday = str((datetime.now() - timedelta(days=1)).date())
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_DISCOUNT',
            'discount_applies_to': 'VALUE_MATCHING',
            'discount': 20,
            'require': ujson.dumps({
                "invoice_match":{"sale": [1000038, 1000039]}
            }),
            'effective_time': yesterday,
            'expiration_time': yesterday,
        }
        self._post_coupon(coupon_values)

        # Coupon B, which gives -50% on orders for more than 50 yuan.
        # It is stackable. It is only valid at the Qianmen shop.
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_DISCOUNT',
            'stackable': 'True',
            'discount_applies_to': 'VALUE_INVOICED',
            'discount': 50,
            'require': ujson.dumps({
                "invoice_match": {
                    "shop": [1000008],
                    "operation": "SUM_PRICE",
                    "more_than": 50,
                    "equal": 50,
                },
            }),
        }
        self._post_coupon(coupon_values)

        # Coupon C, which gives -30% for orders of more than 60 yuan.
        # This coupon is not stackable !
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_DISCOUNT',
            'discount_applies_to': 'VALUE_INVOICED',
            'discount': 30,
            'require': ujson.dumps({
                "invoice_match": {
                    "operation": "SUM_PRICE",
                    "more_than": 60,
                    "equal": 60,
                },
            }),
        }
        self._post_coupon(coupon_values)

        # Coupon D, which gives -10% on hot drinks. It is stackable,
        # but only valid at the Qianmen shop.
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_DISCOUNT',
            'stackable': 'True',
            'discount_applies_to': 'VALUE_MATCHING',
            'discount': 10,
            'require': ujson.dumps({
                "invoice_match":{
                    "sale": [1000038, 1000039],
                    "shop": [1000008],
                }
            }),
        }
        self._post_coupon(coupon_values)

        # The customer orders 1 三文鱼贝果, 2 菠萝包 and 1 鸳鸯咖啡
        # at Dawanglu. Coupon C is applied.
        wwwOrder = [
            {'id_sale': 1000034,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000037,
             'id_variant': 0,
             'quantity': 2,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000039,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000007,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 6)
            discount = 0.3
            self._check_order_item(all_order_items[0], 1000034,
                                   '三文鱼贝果', 1, 30)
            self._check_order_item(all_order_items[1], 1000037,
                                   '菠萝包', 2, 8)
            self._check_order_item(all_order_items[2], 1000039,
                                   '鸳鸯咖啡', 1, 16)
            self._check_order_item(all_order_items[3], 1000034,
                                   '', 1, - 30 * discount)
            self._check_order_item(all_order_items[4], 1000037,
                                   '', 2, - 8 * discount)
            self._check_order_item(all_order_items[5], 1000039,
                                   '', 1, - 16 * discount)

        # The customer makes the same order at Qianmen.
        # Coupon B & D are applied.
        wwwOrder = [
            {'id_sale': 1000034,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000037,
             'id_variant': 0,
             'quantity': 2,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000039,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            discount = 0.5
            self.assertEquals(len(all_order_items), 7)
            self._check_order_item(all_order_items[0], 1000034,
                                   '三文鱼贝果', 1, 30)
            self._check_order_item(all_order_items[1], 1000037,
                                   '菠萝包', 2, 8)
            self._check_order_item(all_order_items[2], 1000039,
                                   '鸳鸯咖啡', 1, 16)
            self._check_order_item(all_order_items[3], 1000034,
                                   '', 1, - 30 * discount)
            self._check_order_item(all_order_items[4], 1000037,
                                   '', 2, - 8 * discount)
            self._check_order_item(all_order_items[5], 1000039,
                                   '', 1, - 16 * discount)
            self._check_order_item(all_order_items[6], 1000039,
                                   '', 1, - 16 * 0.1)

        # The customer orders 1 菠萝包 and 1 鸳鸯咖啡 at Qianmen,
        # Coupon D is applied.
        wwwOrder = [
            {'id_sale': 1000037,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000039,
             'id_variant': 0,
             'quantity': 1,
             'id_shop': 1000008,
             'id_type': 0,
             'id_price_type': 0,
             'id_weight_type': 0},
        ]
        id_order = self.success_wwwOrder(
            self.telephone, self.shipaddr, self.billaddr, wwwOrder)
        with db_utils.get_conn() as conn:
            all_order_items = get_order_items(conn, id_order)
            self.assertEquals(len(all_order_items), 3)
            discount = -0.1
            self._check_order_item(all_order_items[0], 1000037,
                                   '菠萝包', 1, 8)
            self._check_order_item(all_order_items[1], 1000039,
                                   '鸳鸯咖啡', 1, 16)
            self._check_order_item(all_order_items[2], 1000039,
                                   '', 1, 16 * discount)

