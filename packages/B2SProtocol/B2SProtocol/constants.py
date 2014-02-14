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

class SHIPMENT_STATUS(CustomEnum):
    PACKING = 1
    DELAYED = 2
    DELIVER = 3


class SHIPPING_CALCULATION_METHODS(CustomEnum):
    FREE_SHIPPING = 1
    FLAT_RATE = 2
    CARRIER_SHIPPING_RATE = 3
    CUSTOM_SHIPPING_RATE = 4
    INVOICE = 5
