import urllib
from enum import Enum
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME

class CustomEnum(Enum):
    @classmethod
    def toDict(self):
        result = {}
        for k, v in self.__dict__.iteritems():
            if k.startswith('__'):
                continue
            result[k] = v
        return result

class ADDR_TYPE(CustomEnum):
    Shipping = 0
    Billing = 1

class FRT_ROUTE_ROLE(CustomEnum):
    HOMEPAGE = "HOMEPAGE"
    USER_AUTH = "USER_AUTH"
    USER_INFO = "USER_INFO"
    PRDT_LIST = "PRDT_LIST"
    PRDT_INFO = "PRDT_INFO"
    TYPE_LIST = "TYPE_LIST"
    BASKET = "BASKET"
    ORDER_LIST = "ORDER_LIST"
    ORDER_INFO = "ORDER_INFO"
    ORDER_AUTH = "ORDER_AUTH"
    ORDER_USER = "ORDER_USER"
    ORDER_ADDR = "ORDER_ADDR"
    ORDER_INVOICES = 'ORDER_INVOICES'

class Redirection:
    def __init__(self, url, err):
        self.url = url
        self.err = err

    @property
    def redirect_to(self):
        redirect_to = self.url
        if self.err:
            redirect_to += "?%s" % urllib.urlencode({'err': self.err})
        return redirect_to


CURR_USER_BASKET_COOKIE_NAME = "CURR_%s" % USER_BASKET_COOKIE_NAME

