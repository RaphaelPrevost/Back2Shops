# users.backtoshops.com settings
from settings_base import *

PRODUCTION = True
ADM_ROOT_URI = "http://188.165.192.57"
FIN_ROOT_URI = "http://188.165.192.57:9000"
SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'USR': 'http://localhost:8100/webservice/1.0/pub/apikey.pem',
    'ADM': '%s/webservice/1.0/pub/apikey.pem' % ADM_ROOT_URI,
        'FIN': '%s/webservice/1.0/pub/apikey.pem' % FIN_ROOT_URI
}

# TODO: uncommon this after go live
#PAYPAL_SERVER = "https://www.paypal.com/cgi-bin/webscr"

