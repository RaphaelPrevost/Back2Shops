# users.backtoshops.com settings
from settings_base import *

PRODUCTION = True
ADM_ROOT_URI = "http://188.165.192.57"
SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'USR': 'http://localhost:8100/webservice/1.0/pub/apikey.pem',
    'ADM': '%s/webservice/1.0/pub/apikey.pem' % ADM_ROOT_URI
}


