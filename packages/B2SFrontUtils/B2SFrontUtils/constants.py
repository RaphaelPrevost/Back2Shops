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
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    GET_USERINFO = "GET_USERINFO"
    SET_USERINFO = "SET_USERINFO"
    AUX = "AUX"
    GET_SALES = "GET_SALES"

class HTTP_METHOD(CustomEnum):
    GET = "GET"
    POST = "POST"


USR_API_SETTINGS = {
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
    }
}

