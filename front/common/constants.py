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

#TODO move to B2SProtocol later
class FRT_ROUTE_ROLE(CustomEnum):
    HOMEPAGE = "HOMEPAGE"
    USER_INFO = "USER_INFO"
    PRDT_LIST = "PRDT_LIST"
    PRDT_INFO = "PRDT_INFO"
    TYPE_LIST = "TYPE_LIST"
    BASKET = "BASKET"
    ORDER_INVOICES = 'ORDER_INVOICES'
