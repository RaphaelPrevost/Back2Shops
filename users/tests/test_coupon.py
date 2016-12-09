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

from common.test_utils import BaseTestCase
from common.test_utils import is_backoffice_server_running

SKIP_REASON = "Please stop backoffice server before running this test"

class TestCoupon(BaseTestCase):
    def setUp(self):
        super(TestCoupon, self).setUp()
        self.id_brand = 1000001
        self.bo_user = 1000002

    def _list_coupons(self, params=None):
        query = {
            'id_brand': self.id_brand,
            'debugging': 'true',
        }
        if params:
            query.update(params)
        url = "webservice/1.0/private/coupon/list?%s" % urllib.urlencode(query)
        resp = self.b._access(url)
        data = xmltodict.parse(resp.get_data())
        if not data.get('coupons', {}).get('coupon'):
            return []
        elif isinstance(data.get('coupons', {}).get('coupon'), list):
            return data['coupons']['coupon']
        else:
            return [data['coupons']['coupon']]

    def _post_coupon(self, values):
        values.update({
            'id_issuer': self.id_brand,
            'debugging': 'true',
        })
        resp = self.b._access("webservice/1.0/private/coupon", values)
        data = xmltodict.parse(resp.get_data())
        id_coupon = data.get('coupons', {}).get('coupon', {}).get('@id')
        self.assert_(isinstance(id_coupon, basestring) and id_coupon.isdigit())
        return id_coupon

    @unittest.skipUnless(not is_backoffice_server_running(), SKIP_REASON)
    def test_sale_discount_coupon(self):
        id_sale = 1000001
        today = str(datetime.now().date())
        coupon_values = {
            'author': self.bo_user,
            'reward_type': 'COUPON_DISCOUNT',
            'discount_applies_to': 'VALUE_MATCHING',
            'discount': 5,
            'require': ujson.dumps({
                "invoice_match":{"sale": [id_sale]}
            }),
            'effective_time': today,
            'expiration_time': today,
        }

        # check coupon list before create new coupon
        coupons_data = self._list_coupons(params={'id_item': id_sale})
        num = len(coupons_data)

        # create new coupon
        coupon_values.update({'action': 'create'})
        id_coupon = self._post_coupon(coupon_values)
        coupons_data = self._list_coupons(params={'id_item': id_sale})
        self.assertEquals(len(coupons_data), num + 1)
        self.assertEquals(
            xmltodict.unparse(OrderedDict([(u'coupon', coupons_data[-1])])),
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<coupon id="%s" issuer="%s" stackable="false" author="%s">'
                '<type>COUPON_DISCOUNT</type>'
                '<desc></desc>'
                '<password></password>'
                '<valid from="%s 00:00:00" to="%s 23:59:59"></valid>'
                '<redeemable always="true"></redeemable>'
                '<require order="any">'
                    '<order match="sale" id="%s"></order>'
                '</require>'
                '<reward>'
                    '<rebate type="VALUE_MATCHING">5.0</rebate>'
                '</reward>'
            '</coupon>'
            % (id_coupon, self.id_brand, self.bo_user,
               today, today, id_sale)
        )

        # expired coupon
        coupon_values.update({
            'action': 'update',
            'id_coupon': id_coupon,
            'expiration_time': str(datetime.now())[:19],
        })
        id_coupon = self._post_coupon(coupon_values)
        coupons_data = self._list_coupons(params={'id_item': id_sale})
        self.assertEquals(len(coupons_data), num)
        self.assertNotEquals(coupons_data[-1]['@id'], id_coupon)

        # coupon without expiration_time
        coupon_values.pop('expiration_time')
        id_coupon = self._post_coupon(coupon_values)
        coupons_data = self._list_coupons(params={'id_item': id_sale})
        self.assertEquals(len(coupons_data), num + 1)
        self.assertEquals(coupons_data[-1]['@id'], id_coupon)

        # delete coupon
        self._post_coupon({
            'action': 'delete',
            'id_coupon': id_coupon,
        })
        coupons_data = self._list_coupons(params={'id_item': id_sale})
        self.assertEquals(len(coupons_data), num)
        self.assertNotEquals(coupons_data[-1]['@id'], id_coupon)

    @unittest.skipUnless(not is_backoffice_server_running(), SKIP_REASON)
    def test_store_credit_coupon(self):
        today = str(datetime.now().date())
        id_shop = 1000001
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_CURRENCY',
            'store_credit_amount': 10,
            'store_credit_currency': 'EUR',
            'require': ujson.dumps({
                "invoice_match":{"shop": [id_shop]}
            }),
            'effective_time': today,
            'expiration_time': today,
        }
        id_coupon = self._post_coupon(coupon_values)
        coupons_data = self._list_coupons(params={'id_shop': id_shop})
        self.assert_(len(coupons_data) > 0)
        self.assertEquals(
            xmltodict.unparse(OrderedDict([(u'coupon', coupons_data[-1])])),
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<coupon id="%s" issuer="%s" stackable="true" author="%s">'
                '<type>COUPON_CURRENCY</type>'
                '<desc></desc>'
                '<password></password>'
                '<valid from="%s 00:00:00" to="%s 23:59:59"></valid>'
                '<redeemable always="true"></redeemable>'
                '<require order="any">'
                    '<order match="shop" id="%s"></order>'
                '</require>'
                '<reward>'
                    '<credit currency="EUR">10.0</credit>'
                '</reward>'
            '</coupon>'
            % (id_coupon, self.id_brand, self.bo_user,
               today, today, id_shop)
        )

        self._post_coupon({
            'action': 'delete',
            'id_coupon': id_coupon,
        })
        coupons_data = self._list_coupons(params={'id_shop': id_shop})
        self.assertNotEquals(coupons_data[-1]['@id'], id_coupon)

    @unittest.skipUnless(not is_backoffice_server_running(), SKIP_REASON)
    def test_give_away_coupon(self):
        today = str(datetime.now().date())
        id_item_brand = 1000001
        coupon_values = {
            'action': 'create',
            'author': self.bo_user,
            'reward_type': 'COUPON_GIVEAWAY',
            'require': ujson.dumps({
                "invoice_match": {
                    "brand": [id_item_brand],
                    "operation": "SUM_PRICE",
                    "more_than": 100,
                    "equal": 100,
                },
            }),
            'gift': ujson.dumps([{"id": 1000001, "quantity":1},
                                 {"id": 1000002, "quantity":2}]),
            'effective_time': today,
            'expiration_time': today,
        }
        id_coupon = self._post_coupon(coupon_values)
        coupons_data = self._list_coupons(params={'item_brand': id_item_brand})
        self.assert_(len(coupons_data) > 0)
        self.assertEquals(
            xmltodict.unparse(OrderedDict([(u'coupon', coupons_data[-1])])),
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<coupon id="%s" issuer="%s" stackable="false" author="%s">'
                '<type>COUPON_GIVEAWAY</type>'
                '<desc></desc>'
                '<password></password>'
                '<valid from="%s 00:00:00" to="%s 23:59:59"></valid>'
                '<redeemable always="true"></redeemable>'
                '<require order="any">'
                    '<order match="brand" id="%s"></order>'
                    '<threshold sum="price" must="GTE">100.0</threshold>'
                '</require>'
                '<reward>'
                    '<gift quantity="1">1000001</gift>'
                    '<gift quantity="2">1000002</gift>'
                '</reward>'
            '</coupon>'
            % (id_coupon, self.id_brand, self.bo_user,
               today, today, id_item_brand)
        )

        self._post_coupon({
            'action': 'delete',
            'id_coupon': id_coupon,
        })
        coupons_data = self._list_coupons(params={'item_brand': id_item_brand})
        self.assertNotEquals(coupons_data[-1]['@id'], id_coupon)
