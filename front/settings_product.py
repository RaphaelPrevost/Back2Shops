# frontend settings
from settings_local import *

PRODUCTION = True

USR_ROOT_URI = "http://92.222.30.2"
SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
}

FRONT_ROOT_URI = "http://92.222.30.5"
PP_SUCCESS = "%s/paypal/%%(id_trans)s/success" % FRONT_ROOT_URI
PP_FAILURE = "%s/paypal/%%(id_trans)s/failure" % FRONT_ROOT_URI

PB_SUCCESS = "%s/paybox/%(id_trans)s/success" % FRONT_ROOT_URI
PB_ERROR = "%s/paybox/%(id_trans)s/error" % FRONT_ROOT_URI
PB_CANCEL = "%s/paybox/%(id_trans)s/cancel" % FRONT_ROOT_URI
PB_WAITING = "%s/paybox/%(id_trans)s/waiting" % FRONT_ROOT_URI

BRAND_ID = "1"
