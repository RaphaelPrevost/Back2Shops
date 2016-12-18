# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


# users.backtoshops.com settings
import os
from common.constants import HASH_ALGORITHM
from B2SProtocol.constants import PAYMENT_TYPES

DEBUG = True
SERVER_PORT = 8100 # for development only

DATABASE = {
    'NAME': 'users',
    'USER': 'postgres',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '5432',
    'MAX_CONN': 50,
    'CONN_EXPIRATION': 1, #minute
}
CENTRAL_REDIS = {
    'HOST': 'localhost',
    'PORT': 6379,
    'TEST_PORT': 6279
}

DEFAULT_REDIS_CACHE_TTL = 15 * 60 # now it's used for only TypesCacheProxy

DEFAULT_PASSWORD_HASH_ALGORITHM = HASH_ALGORITHM.WHIRLPOOL
DEFAULT_API_KEY_HASH_ALGORITHM = HASH_ALGORITHM.SHA256
HASH_MIN_ITERATIONS = 2
HASH_MAX_ITERATIONS = 256
USER_CREATION_CAPTCHA = "1234" # temporary solution for now

USER_AUTH_COOKIE_EXPIRES = 8 * 3600

SUPPORTED_MAJOR_COUNTRIES = ['US', 'CA', 'CN']

LOG_CONFIG_FILE = 'logging.cfg'
BUGZ_SCOUT_REPORT = {
    'url': 'http://dragondollar.fogbugz.com/scoutSubmit.asp',
    'user_name': 'bugwatch@dragondollar.com',
    'project': 'Dragon Dollar',
    'area': 'user',
}

HMAC_KEY_SIZE = 128
HMAC_KEY_FILE_PATH = 'hmac.pem'

ADM_ROOT_URI = "http://localhost:8000"
USR_ROOT_URI = "http://localhost:8100"
FIN_ROOT_URI = "http://localhost:9000"
VSL_ROOT_URI = "http://localhost:8700"
AST_ROOT_URI = "http://localhost:9300"
FRONT_ROOT_URI = "http://localhost:9500"

SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FIN': os.path.join(FIN_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'VSL': os.path.join(VSL_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FRO': os.path.join(FRONT_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'AST': os.path.join(AST_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
}

FRONT_RESET_PASSWORD_URL = "%s/reset_password" % FRONT_ROOT_URI
RESET_PASSWORD_EMAIL_SUBJECT = "Demande de nouveau mot de passe"
RESET_PASSWORD_REQUEST_EXPIRES = 3600

FRONT_ORDER_INVOICE_URL = "%s/orders/%%(id_order)s" % FRONT_ROOT_URI
ORDER_EMAIL_SUBJECT = "Confirmation de votre commande"

PRIVATE_KEY_PATH = 'static/keys/usr_pri.key'
PUB_KEY_PATH = 'static/keys/usr_pub.key'

ORDERS_QUERY_LIMIT = 100
RUNNING_TEST = False

# config to see decrypt content for response,
# only used for debugging
CRYPTO_RESP_DEBUGING = True

PRODUCTION = False

INVOICE_VALIDATE_PATH = 'files/invoice/invoice.dtd'
INVOICE_XSLT_PATH = 'files/invoice/invoice.%s.xsl'
SALES_VALIDATE_PATH = 'files/sales/sales.dtd'
SALEINFO_VALIDATE_PATH = 'files/sales/sale_info.dtd'
SHOPS_VALIDATE_PATH = 'files/shops/shops.dtd'
SHOPINFO_VALIDATE_PATH = 'files/shops/shop_info.dtd'
ORDER_XSLT_PATH = 'files/order/order.%s.xsl'

SEND_EMAILS = False
SERVICE_EMAIL = 'serviceclients@breuer.fr'
MAIL_HOST = 'smtp.gmail.com:587'
MAIL_FROM_USER = 'xxx'
MAIL_FROM_PASS = 'xxx'

# Paypal
PAYMENT_PAYPAL_GATEWAY = "%s/payment/paypal/%%(id_trans)s/gateway" % USR_ROOT_URI
PAYMENT_PAYPAL_RETURN = "%s/payment/paypal/%%(id_trans)s/process" % USR_ROOT_URI
PAYMENT_PAYPAL_CANCEL = "%s/paypal/%%(id_trans)s/cancel" % FRONT_ROOT_URI

PAYPAL_SERVER = "https://www.sandbox.paypal.com/cgi-bin/webscr"
FIN_PAYPAL_TRANS = '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI

# Paybox
PAYMENT_PAYBOX_SUCCESS = "%s/paybox/%%(id_trans)s/success" % FRONT_ROOT_URI
PAYMENT_PAYBOX_FAILURE = "%s/paybox/%%(id_trans)s/failure" % FRONT_ROOT_URI
PAYMENT_PAYBOX_CANCEL = "%s/paybox/%%(id_trans)s/cancel" % FRONT_ROOT_URI
PAYMENT_PAYBOX_WAITING = "%s/paybox/%%(id_trans)s/waiting" % FRONT_ROOT_URI
PAYMENT_PAYBOX_GATEWAY = "%s/payment/paybox/%%(id_trans)s/gateway" % USR_ROOT_URI

# Stripe
PAYMENT_STRIPE_PROCESS = "%s/payment/stripe/%%(id_trans)s/process" % USR_ROOT_URI 
FIN_PAYMENT_STRIPE_CHARGE_URL = '%s/webservice/1.0/pub/stripe/trans/%%(id_trans)s/charge' % FIN_ROOT_URI


FIN_PAYMENT_NOTIFY_URL = {
    PAYMENT_TYPES.PAYPAL: '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI,
    PAYMENT_TYPES.PAYBOX: '%s/webservice/1.0/pub/paybox/trans/%%(id_trans)s' % FIN_ROOT_URI,
    PAYMENT_TYPES.STRIPE: '%s/webservice/1.0/pub/stripe/trans/%%(id_trans)s' % FIN_ROOT_URI,
}

SELLER_EMAIL = 'business@infinite-code.com'

CURRENCY_EX_RATE = {
    'EUR': {'EUR': 1.0,
            'USD': 1.38251},

    'USD': {'USD': 1.0,
            'EUR': 0.72332}
}

LOCALE_LANGUAGES = ['zh', 'en', 'fr']
DEFAULT_LANGUAGE = 'en'

