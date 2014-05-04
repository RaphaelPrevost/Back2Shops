# finance.backtoshops.com settings
import os
from settings_base import *

PRODUCTION = True
ADM_ROOT_URI = "http://188.165.192.57"
SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
    'ADM': os.path.join(ADM_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem')
}

# TODO: change to real paypal seller email
SELLER_EMAIL = 'test@infinite-code.com'
