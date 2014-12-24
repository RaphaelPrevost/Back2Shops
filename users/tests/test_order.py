# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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

from common.test_utils import is_backoffice_server_running
from tests.base_order_test import BaseOrderTestCase

SKIP_REASON = "Please run backoffice server before running this test"

class TestOrder(BaseOrderTestCase):
    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def testOrderInUniqueShop(self):
        # test posOrder items in unique shop.
        # order: shop:1
        #        barcode:11111, barcode:11112 for sale:1
        #        barcode:22221, barcode:22222 for sale:2
        upc_shop = '11111'
        posOrder = [('11111', 1, 0),
                    ('11112', 2, 0),
                    ('22221', 3, 0),
                    ('22222', 4, 0)]
        self.success_posOrder(self.telephone, upc_shop, posOrder)

        # test wwwOrder items in unique shop.
        # order:
        wwwOrder = [
            {'id_sale': 1000001,
             'id_variant': 1000001,
             'quantity': 5,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000001,
             'id_variant': 1000002,
             'quantity': 6,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000002,
             'id_variant': 1000003,
             'quantity': 7,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000002,
             'id_variant': 1000004,
             'quantity': 8,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0}
        ]
        self.success_wwwOrder(self.telephone,
                              self.shipaddr,
                              self.billaddr,
                              wwwOrder)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def __testOrderInDiffShopSameBrand(self):
        # test posOrder items in shop 1, brand 1.
        # order: shop:1,
        #        barcode:11111, barcode:11112 for sale:1
        upc_shop = '11111'
        posOrder = [('11111', 1, 0),
                    ('11112', 2, 0)]
        self.success_posOrder(self.telephone,
                              upc_shop,
                              posOrder)

        # test posOrder items in shop 2, brand 1.
        #        shop:2,
        #        barcode:33331, barcode:33332 for sale:3
        upc_shop = '22222'
        posOrder = [('33331', 3, 0),
                    ('33332', 4, 0)]
        self.success_posOrder(self.telephone,
                              upc_shop,
                              posOrder)

        # test wwwOrder items in unique shop.
        # order:
        wwwOrder = [
            {'id_sale': 1000001,
             'id_variant': 1000001,
             'quantity': 5,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000001,
             'id_variant': 1000002,
             'quantity': 6,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000003,
             'id_variant': 1000005,
             'quantity': 7,
             'id_shop': 1000002,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000003,
             'id_variant': 1000006,
             'quantity': 8,
             'id_shop': 1000002,
             'id_price_type': 0,
             'id_weight_type': 0}
        ]
        self.success_wwwOrder(self.telephone,
                              self.shipaddr,
                              self.billaddr,
                              wwwOrder)

    @unittest.skipUnless(is_backoffice_server_running(), SKIP_REASON)
    def __testOrderInDiffShopDiffBrand(self):
        # test posOrder items in shop 1, brand 1.
        # order: shop:1,
        #        barcode:11111, barcode:11112 for sale:1
        upc_shop = '11111'
        posOrder = [('11111', 1, 0),
                    ('11112', 2, 0)]
        self.success_posOrder(self.telephone, upc_shop, posOrder)

        # test posOrder items in shop 3, brand 2.
        #        shop:3,
        #        barcode:44441, barcode:44442 for sale:4
        upc_shop = '33333'
        posOrder = [('44441', 3, 0),
                    ('44442', 4, 0)]
        self.success_posOrder(self.telephone, upc_shop, posOrder)

        # test wwwOrder items in unique shop.
        # order:
        wwwOrder = [
            {'id_sale': 1000001,
             'id_variant': 1000001,
             'quantity': 5,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000001,
             'id_variant': 1000002,
             'quantity': 6,
             'id_shop': 1000001,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000004,
             'id_variant': 1000007,
             'quantity': 7,
             'id_shop': 1000003,
             'id_price_type': 0,
             'id_weight_type': 0},
            {'id_sale': 1000004,
             'id_variant': 1000008,
             'quantity': 8,
             'id_shop': 1000003,
             'id_price_type': 0,
             'id_weight_type': 0}
        ]
        self.success_wwwOrder(self.telephone,
                              self.shipaddr,
                              self.billaddr,
                              wwwOrder)

