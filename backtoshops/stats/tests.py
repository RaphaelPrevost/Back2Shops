""" Test order statistics status.
"""
import httplib
import urllib
import ujson

from datetime import datetime, timedelta
from django.test import Client
from django.test import TestCase
from stats.models import Orders


DT_FORMAT = "%Y-%m-%d"
class StatsOrderTest(TestCase):
    fixtures = ['test_data.xml',]
    def setUp(self):
        # item 1 - (1000001): Brand A(1000001) shop 1(1000001), completed
        # item 2 - (1000003): Brand A(1000001) shop 2(1000002), waiting shipping
        # item 3 - (1000012): Brand B(1000003) internal,        waiting shipping
        # item 4 - (1000006): Brand B(1000003) shop 6(1000006), completed

        # Brand A's admin, shopkeeper 1
        # Brand B's admin, shopkeeper 6 (have internal authentication).

        common_values = {'users_id': 100,
                  'order_id': 101}

        today = datetime.utcnow().date()
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()

        item1_value = {'brand_id': 1000001,
                       'shop_id': 1000001,
                       'waiting_payment_date': today,
                       'waiting_shipping_date': today,
                       'completed_date': today}

        item2_value = {'brand_id': 1000001,
                       'shop_id': 1000002,
                       'waiting_payment_date': yesterday,
                       'waiting_shipping_date': yesterday}

        item3_value = {'brand_id': 1000003,
                       'shop_id': 0,
                       'waiting_payment_date': today,
                       'waiting_shipping_date': today}

        item4_value = {'brand_id': 1000003,
                       'shop_id': 1000006,
                       'waiting_payment_date': yesterday,
                       'waiting_shipping_date': today,
                       'completed_date': today}

        items = [item1_value, item2_value, item3_value, item4_value]

        for item in items:
            Orders.objects.create(
                users_id=common_values['users_id'],
                order_id=common_values['order_id'],
                brand_id=item['brand_id'],
                shop_id=item['shop_id'],
                pending_date = item.get('pending_date'),
                waiting_payment_date=item.get('waiting_payment_date'),
                waiting_shipping_date=item.get('waiting_shipping_date'),
                completed_date=item.get('completed_date')
            )

        self.client = Client(enforce_csrf_checks=True)

    def test_order_status(self):
        from_ = datetime.utcnow().date().strftime(DT_FORMAT)
        to = (datetime.utcnow() + timedelta(days=1)).date().strftime(DT_FORMAT)
        params = urllib.urlencode({'from': from_, 'to': to})
        url = '/stats/orders' + "?" + params

        brand1_admin = {'username': 'test_user1_1000000',
                        'password': 'user14u'}

        brand2_admin = {'username': 'test_user3_1000000',
                        'password': 'user34u'}

        shopkeeper1 = {'username': 'shopkeeper1',
                       'password': 'shopkeeper1'}

        shopkeeper2 = {'username': 'shopkeeper2',
                       'password': 'shopkeeper2'}

        shopkeeper6 = {'username': 'shopkeeper6',
                       'password': 'shopkeeper6'}

        # case1: brand1 admin, expect waiting shipping status.
        expect = {"1":0,"2":0,"3":1,"4":0}
        self._status_check(brand1_admin, url, expect)

        # case2: shop keeper 1, expect completed status
        expect = {"1":0,"2":0,"3":0,"4":1}
        self._status_check(shopkeeper1, url, expect)

        # case3: shop keeper 2, expect waiting shipping status
        expect = {"1":0,"2":0,"3":1,"4":0}
        self._status_check(shopkeeper2, url, expect)

        # case4: brand2 admin, expect waiting shipping status
        expect = {"1":0,"2":0,"3":1,"4":0}
        self._status_check(brand2_admin, url, expect)

        # case5: shop keeper 6, expect waiting shipping status
        expect = {"1":0,"2":0,"3":1,"4":0}
        self._status_check(shopkeeper6, url, expect)

    def _status_check(self, user, url, expect):
        login = self.client.login(**user)
        self.assertTrue(login)

        response = self.client.get(url)
        self.assertEqual(response.status_code, httplib.OK)

        orders = ujson.loads(response.content)
        self.assertDictEqual(orders, expect)
        self.client.logout()
