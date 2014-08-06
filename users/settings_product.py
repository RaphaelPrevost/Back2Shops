# users.backtoshops.com settings
from settings_base import *

PRODUCTION = True
ADM_ROOT_URI = "http://37.187.48.33"
USR_ROOT_URI = "http://92.222.30.2"
FIN_ROOT_URI = "http://92.222.30.3"
FRONT_ROOT_URI = "http://92.222.30.5" # for testing only

SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'USR': '%s/webservice/1.0/pub/apikey.pem' % USR_ROOT_URI,
    'ADM': '%s/webservice/1.0/pub/apikey.pem' % ADM_ROOT_URI,
    'FIN': '%s/webservice/1.0/pub/apikey.pem' % FIN_ROOT_URI,
    'FRO': '%s/webservice/1.0/pub/apikey.pem' % FRONT_ROOT_URI,
}


PAYMENT_PAYPAL_GATEWAY = "%s/payment/%%(id_trans)s/gateway" % USR_ROOT_URI
PAYMENT_PAYPAL_RETURN = "%s/payment/%%(id_trans)s/process" % USR_ROOT_URI
PAYMENT_PAYPAL_CANCEL = "%s/payment/%%(id_trans)s/cancel" % FRONT_ROOT_URI

PAYMENT_PAYBOX_SUCCESS = "%s/payment/paybox/%%(id_trans)s/success" % FRONT_ROOT_URI
PAYMENT_PAYBOX_FAILURE = "%s/payment/paybox/%%(id_trans)s/failure" % FRONT_ROOT_URI
PAYMENT_PAYBOX_CANCEL = "%s/payment/paybox/%%(id_trans)s/cancel" % FRONT_ROOT_URI
PAYMENT_PAYBOX_WAITING = "%s/payment/paybox/%%(id_trans)s/waiting" % FRONT_ROOT_URI
PAYMENT_PAYBOX_GATEWAY = "%s/payment/paybox/%%(id_trans)s/gateway" % USR_ROOT_URI

PAYPAL_SERVER = "https://www.sandbox.paypal.com/cgi-bin/webscr"

FIN_PAYMENT_NOTIFY_URL = {
    PAYMENT_TYPES.PAYPAL: '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI,
    PAYMENT_TYPES.PAYBOX: '%s/webservice/1.0/pub/paybox/trans/%%(id_trans)s' % FIN_ROOT_URI,
}

SELLER_EMAIL = 'business@infinite-code.com'
CURRENCY_EX_RATE = {
    'EUR': {'EUR': 1.0,
            'USD': 1.38251},

    'USD': {'USD': 1.0,
            'EUR': 0.72332}
}

# TODO: uncommon this after go live
#PAYPAL_SERVER = "https://www.paypal.com/cgi-bin/webscr"

