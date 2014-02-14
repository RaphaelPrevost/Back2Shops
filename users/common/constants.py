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

class FIELD_TYPE(CustomEnum):
    TEXT = "text"
    SELECT = "select"
    RADIO = "radio"
    FIELDSET = "fieldset"
    AJAX = "ajax"

class GENDER(CustomEnum):
    Male = "M"
    Female = "F"
    Other = "O"

class ADDR_TYPE(CustomEnum):
    Shipping = 0
    Billing = 1

class RESP_RESULT(CustomEnum):
    S = "SUCCESS"
    F = "FAILURE"

class HASH_ALGORITHM(CustomEnum):
    WHIRLPOOL = 1
    SHA256 = 2

class INVOICE_STATUS(CustomEnum):
    INVOICE_OPEN = 1
    INVOICE_PART = 2
    INVOICE_VOID = 3
    INVOICE_PAID = 4
    INVOICE_LATE = 5

class RETURN_STATUS(CustomEnum):
    RETURN_ELIGIBLE = 1
    RETURN_REJECTED = 2 #1 << 1
    RETURN_RECEIVED = 4 #1 << 2
    RETURN_EXAMINED = 8 #1 << 3
    RETURN_ACCEPTED = 16 #1 << 4
    RETURN_REJECTED = 32 #1 << 5
    RETURN_PROPOSAL = 64 #1 << 6
    RETURN_REFUNDED = 128 #1 << 7
    RETURN_REJECTED_FRAUD = 256 #1 << 8
    RETURN_REJECTED_INVAL = 512 #1 << 9
    RETURN_PROPOSAL_ACCEPT = 1024 #1 << 10
    RETURN_PROPOSAL_REJECT = 2048 #1 << 11

class ORDER_STATUS(CustomEnum):
    PENDING = 1
    AWAITING_PAYMENT = 2
    AWAITING_SHIPPING = 3
    COMPLETED = 4

HASH_ALGORITHM_NAME = {
    HASH_ALGORITHM.WHIRLPOOL: "whirlpool",
    HASH_ALGORITHM.SHA256: "sha256",
}


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

SALE_CACHED_QUERY = 'SALE_CACHED_QUERY:%s'
SALES_QUERY = 'SALES:QUERY:%s'

BARCODE = 'BARCODE:%s:SHOP:%s'
BARCODE_VARIANT_ID = 'barcode_variant_id'
BARCODE_ATTR_ID = 'barcode_attribute_id'
BARCODE_SALE_ID = 'barcode_sale_id'

SHOP_WITH_BARCODE = 'SHOP_WITH_BARCODE:%s'
GLOBAL_MARKET = '0'
