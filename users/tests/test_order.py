import ujson
import unittest

from common.utils import _parse_auth_cookie
from common.test_utils import is_backoffice_server_running
from tests.base_order_test import BaseOrderTestCase
from B2SUtils import db_utils

SKIP_REASON = "Please run backoffice server before running this test"

class TestOrder(BaseOrderTestCase):
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
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
            {'id_sale': 1000001, 'id_variant': 1000001, 'quantity': 5, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000001, 'id_variant': 1000002, 'quantity': 6, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000002, 'id_variant': 1000003, 'quantity': 7, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000002, 'id_variant': 1000004, 'quantity': 8, 'id_shop': 1000001, 'id_weight_type': 0}
        ]
        self.success_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
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
            {'id_sale': 1000001, 'id_variant': 1000001, 'quantity': 5, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000001, 'id_variant': 1000002, 'quantity': 6, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000003, 'id_variant': 1000005, 'quantity': 7, 'id_shop': 1000002, 'id_weight_type': 0},
            {'id_sale': 1000003, 'id_variant': 1000006, 'quantity': 8, 'id_shop': 1000002, 'id_weight_type': 0}
        ]
        self.success_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
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
            {'id_sale': 1000001, 'id_variant': 1000001, 'quantity': 5, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000001, 'id_variant': 1000002, 'quantity': 6, 'id_shop': 1000001, 'id_weight_type': 0},
            {'id_sale': 1000004, 'id_variant': 1000007, 'quantity': 7, 'id_shop': 1000003, 'id_weight_type': 0},
            {'id_sale': 1000004, 'id_variant': 1000008, 'quantity': 8, 'id_shop': 1000003, 'id_weight_type': 0}
        ]
        self.success_wwwOrder(telephone, shipaddr, billaddr, wwwOrder)

