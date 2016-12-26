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


from enum import Enum

class CustomEnum(Enum):
    @classmethod
    def toDict(self):
        result = {}
        for k, v in self.__dict__.iteritems():
            if k.startswith('__'):
                continue
            result[k] = v
        return result

    @classmethod
    def toReverseDict(self):
        result = {}
        for k, v in self.__dict__.iteritems():
            if k.startswith('__'):
                continue
            result[v] = k
        return result


SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
class RESP_RESULT(CustomEnum):
    S = SUCCESS
    F = FAILURE

class SHIPMENT_STATUS(CustomEnum):
    CONFIRMING = 6
    PACKING = 1
    DELAYED = 2
    DELIVER = 3
    DELETED = 4
    FETCHED = 5

class SHIPPING_CALCULATION_METHODS(CustomEnum):
    FREE_SHIPPING = 1
    FLAT_RATE = 2
    CARRIER_SHIPPING_RATE = 3
    CUSTOM_SHIPPING_RATE = 4
    INVOICE = 5
    MANUAL = 6

class ORDER_STATUS(CustomEnum):
    PENDING = 1
    AWAITING_PAYMENT = 2
    AWAITING_SHIPPING = 3
    COMPLETED = 4

class TRANS_STATUS(CustomEnum):
    TRANS_OPEN = 1
    TRANS_PAID = 2

class ORDER_IV_SENT_STATUS(CustomEnum):
    NO_SENT = 1
    PART_SENT = 2
    WAITING_SPM_CREATE = 3
    SENT = 4

class TRANS_PAYPAL_STATUS (CustomEnum):
    COMPLETED = 'completed'
    PENDING = 'pending'

class INVOICE_STATUS(CustomEnum):
    INVOICE_OPEN = 1
    INVOICE_PART = 2
    INVOICE_VOID = 3
    INVOICE_PAID = 4
    INVOICE_LATE = 5

class PAYMENT_TYPES(CustomEnum):
    # make it consistent with table processor in finance database
    PAYPAL = 1
    #VISA_MASTER = 2
    #VISA_MASTER_WITH_3D = 3
    PAYBOX = 4
    STRIPE = 5


FREE_SHIPPING_CARRIER = -1
CUSTOM_SHIPPING_CARRIER = 0

USER_AUTH_COOKIE_NAME = 'USER_AUTH'
USER_BASKET_COOKIE_NAME = 'BASKET'

# central redis key BEGIN
ALL = 'ALL'
SALE = 'SALE:%s'
SALES_FOR_TYPE = 'SALES_FOR_TYPE:%s'
SALES_FOR_CATEGORY = 'SALES_FOR_CATEGORY:%s'
SALES_FOR_SHOP = 'SALES_FOR_SHOP:%s'
SALES_FOR_BRAND = 'SALES_FOR_BRAND:%s'
SALES_VERSION = 'SALES_VERSION'
SALES_ALL = 'SALES:%s'

SHOP = 'SHOP:%s'
SHOPS_FOR_BRAND = 'SHOPS_FOR_BRAND:%s'
SHOPS_FOR_CITY = 'SHOPS_FOR_CITY:%s'
SHOPS_VERSION = 'SHOPS_VERSION'
SHOPS_ALL = 'SHOPS:%s'

GROUP = 'GROUP:%s'
GROUPS_FOR_BRAND = 'GROUPS_FOR_BRAND:%s'
GROUPS_FOR_SHOP = 'GROUPS_FOR_SHOP:%s'
GROUPS_VERSION = 'GROUPS_VERSION'
GROUPS_ALL = 'GROUPS:%s'

SALE_CACHED_QUERY = 'SALE_CACHED_QUERY:%s'
SALES_QUERY = 'SALES:QUERY:%s'

TYPE = 'TYPE:%s'
CATEGORY = 'CATEGORY:%s'
CATEGORY_FOR_BRAND = 'CATEGORY_FOR_BRAND:%s'
TYPES_VERSION = 'TYPES_VERSION'
TYPES_FOR_BRAND = 'TYPE_FOR_BRAND:%s'

TAXES_VERSION = 'TAXES_VERSION'
TAXES_FOR_FO = 'TAX_FOR_FO:%s'

ROUTE = 'ROUTE:%s'
ROUTES_VERSION = 'ROUTES_VERSION'
ROUTES_FOR_BRAND = 'ROUTE_FOR_BRAND:%s'

BRANDSETTING = 'BRAND:%s,SETTING:%s'
BRANDSETTINGS_VERSION = 'SETTINGS_VERSION'

BARCODE = 'BARCODE:%s:SHOP:%s'
BARCODE_VARIANT_ID = 'barcode_variant_id'
BARCODE_ATTR_ID = 'barcode_attribute_id'
BARCODE_SALE_ID = 'barcode_sale_id'

SHOP_WITH_BARCODE = 'SHOP_WITH_BARCODE:%s'
GLOBAL_MARKET = '0'

USER_BASKET = "BASKET:%s"
LOGIN_USER_BASKET_KEY = "USER:%s:BASKET"

INVALIDATE_CACHE_LIST = 'INVALID_CACHE:%s'

# central redis key END


class INVALIDATE_CACHE_OBJ(CustomEnum):
    ROUTES = 'ROUTES'


EURO_UNION_COUNTRIES = (
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
    'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
    'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'GB',
)


SESSION_COOKIE_NAME = 'SESSION'
EXPIRY_FORMAT = '%a, %d %b %Y %H:%M:%S UTC'

