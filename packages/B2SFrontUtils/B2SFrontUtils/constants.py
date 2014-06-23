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
    AUX = "AUX"
    GET_SALES = "GET_SALES"
    GET_TYPES = "GET_TYPES"
    CREATE_ORDER = "CREATE_ORDER"
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
    REMOTE_API_NAME.GET_INVOICES: {
        'url': '/webservice/1.0/private/invoice/get4fuser',
        'method': HTTP_METHOD.GET
    },
    REMOTE_API_NAME.INIT_PAYMENT: {
        'url': '/webservice/1.0/pub/payment/init',
        'method': HTTP_METHOD.POST
    },
    REMOTE_API_NAME.PAYMENT_FORM: {
        'url': '/webservice/1.0/pub/payment/form',
        'method': HTTP_METHOD.POST
    },
}
