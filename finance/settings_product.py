# finance.backtoshops.com settings
import os
from settings_base import *

PRODUCTION = True
LOG_CONFIG_FILE = 'product_logging.cfg'

ADM_ROOT_URI = "http://37.187.48.33"
USR_ROOT_URI = "http://92.222.30.2"
SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
    'ADM': os.path.join(ADM_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem')
}

# TODO: change to real paypal seller email
SELLER_EMAIL = 'business@infinite-code.com'

# TODO: change production values for paybox settings
### Paybox
PAYBOX_REQUEST_URL = 'https://preprod-tpeweb.paybox.com/cgi/MYchoix_pagepaiement.cgi'

# no-3D
PAYBOX_SITE = '1999888'
PAYBOX_RANG = '32'
PAYBOX_IDENTIFIANT = '1686319'

#3D
# PAYBOX_SITE = '1999888'
# PAYBOX_RANG = '43'
# PAYBOX_IDENTIFIANT = '107975626'

#
# PAYBOX_SITE = '7830331'
# PAYBOX_RANG = '16'
# PAYBOX_IDENTIFIANT = '537370176'

PAYBOX_HMAC_KEY = '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF'
# PAYBOX_HMAC_KEY = '11E83FB4C0D2DA9458A7B67463B7A478771CDA3403DBBAB3A871018F78A0DC7DE2939966F4EB1894C550AF236A1A40CFF888E21A1BA5BE60A073F913E226AD2A'
