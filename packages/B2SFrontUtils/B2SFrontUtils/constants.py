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

class REMOTE_API_NAME(CustomEnum):
    GET_ROUTES = "GET_ROUTES"
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    GET_USERINFO = "GET_USERINFO"
    SET_USERINFO = "SET_USERINFO"
    ONLINE = "ONLINE"
    AUX = "AUX"
    GET_SALES = "GET_SALES"
    GET_TYPES = "GET_TYPES"
    CREATE_ORDER = "CREATE_ORDER"
    GET_ORDERS = "GET_ORDERS"
    GET_ORDER_DETAIL = "GET_ORDER_DETAIL"
    GET_SHIPPING_LIST = "GET_SHIPPING_LIST"
    GET_SHIPPING_FEE = "GET_SHIPPING_FEE"
    SET_SHIPPING_CONF = "SET_SHIPPING_CONF"
    REQ_INVOICES = "REQ_INVOICES"
    GET_INVOICES = "GET_INVOICES"
    INIT_PAYMENT = "INIT_PAYMENT"
    PAYMENT_FORM = "PAYMENT_FORM"

class HTTP_METHOD(CustomEnum):
    GET = "GET"
    POST = "POST"


USR_API_SETTINGS = {
    REMOTE_API_NAME.GET_ROUTES: {
        'url': '/webservice/1.0/private/routes/list',
        'method': HTTP_METHOD.GET,
    },
    REMOTE_API_NAME.LOGIN: {
        'url': '/webservice/1.0/pub/connect',
        'method': HTTP_METHOD.POST,
    },
    REMOTE_API_NAME.REGISTER: {
        'url': '/webservice/1.0/pub/account',
        'method': HTTP_METHOD.POST,
    },
    REMOTE_API_NAME.GET_USERINFO: {
        'url': '/webservice/1.0/pub/account',
        'method': HTTP_METHOD.GET,
    },
    REMOTE_API_NAME.SET_USERINFO: {
        'url': '/webservice/1.0/pub/account',
        'method': HTTP_METHOD.POST,
    },
    REMOTE_API_NAME.ONLINE: {
        'url': '/webservice/1.0/pub/online',
        'method': HTTP_METHOD.GET,
    },
    REMOTE_API_NAME.AUX: {
        'url': '/webservice/1.0/pub/JSONAPI',
        'method': HTTP_METHOD.GET,
    },
    REMOTE_API_NAME.GET_SALES: {
        'url': '/webservice/1.0/pub/sales/list',
        'method': HTTP_METHOD.GET,
    },
    REMOTE_API_NAME.GET_TYPES: {
        'url': '/webservice/1.0/pub/types/list',
        'method': HTTP_METHOD.GET
    },
    REMOTE_API_NAME.CREATE_ORDER: {
        'url': '/webservice/1.0/pub/order',
        'method': HTTP_METHOD.POST
    },
    REMOTE_API_NAME.GET_ORDERS: {
        'url': '/webservice/1.0/pub/order/orders',
        'method': HTTP_METHOD.GET
    },
    REMOTE_API_NAME.GET_ORDER_DETAIL: {
        'url': '/webservice/1.0/pub/order/detail',
        'method': HTTP_METHOD.GET
    },
    REMOTE_API_NAME.GET_SHIPPING_LIST: {
        'url': '/webservice/1.0/pub/shipping/list',
        'method': HTTP_METHOD.GET
    },
    REMOTE_API_NAME.GET_SHIPPING_FEE: {
        'url': '/webservice/1.0/pub/shipping/fees',
        'method': HTTP_METHOD.GET
    },
    REMOTE_API_NAME.SET_SHIPPING_CONF: {
        'url': '/webservice/1.0/pub/shipping/conf',
        'method': HTTP_METHOD.POST
    },
    REMOTE_API_NAME.INIT_PAYMENT: {
        'url': '/webservice/1.0/pub/payment/init',
        'method': HTTP_METHOD.POST
    },
    REMOTE_API_NAME.PAYMENT_FORM: {
        'url': '/webservice/1.0/pub/payment/form',
        'method': HTTP_METHOD.POST
    },
    REMOTE_API_NAME.REQ_INVOICES: {
        'url': '/webservice/1.0/pub/invoice/request',
        'method': HTTP_METHOD.POST
    },
    REMOTE_API_NAME.GET_INVOICES: {
        'url': '/webservice/1.0/pub/invoice/get',
        'method': HTTP_METHOD.GET
    },
}
