# users.backtoshops.com settings
import os
from common.constants import HASH_ALGORITHM
from common.constants import PAYMENT_TYPES

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
HASH_MIN_ITERATIONS = 2
HASH_MAX_ITERATIONS = 256
USER_CREATION_CAPTCHA = "1234" # temporary solution for now

USER_AUTH_COOKIE_EXPIRES = 8 * 3600

SUPPORTED_MAJOR_COUNTRIES = ['US', 'CA', 'CN']

LOG_CONFIG_FILE = 'logging.cfg'

HMAC_KEY_SIZE = 128
HMAC_KEY_FILE_PATH = 'hmac.pem'

ADM_ROOT_URI = "http://localhost:8000"
USR_ROOT_URI = "http://localhost:8100"
FIN_ROOT_URI = "http://localhost:9000"
FRONT_ROOT_URI = "http://localhost:9500"

SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FIN': os.path.join(FIN_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FRO': os.path.join(FRONT_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
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

SEND_EMAILS = False
SERVICE_EMAIL = 'serviceclients@breuer.fr'
MAIL_HOST = 'smtp.gmail.com:587'
MAIL_FROM_USER = 'xxx'
MAIL_FROM_PASS = 'xxx'

# Paypal
PAYMENT_PAYPAL_GATEWAY = "%s/payment/paypal/%%(id_trans)s/gateway" % USR_ROOT_URI
PAYMENT_PAYPAL_RETURN = "%s/payment/paypal/%%(id_trans)s/process" % USR_ROOT_URI
PAYMENT_PAYPAL_CANCEL = "%s/paypal/%%(id_trans)s/cancel" % FRONT_ROOT_URI

# Paybox
PAYMENT_PAYBOX_SUCCESS = "%s/paybox/%%(id_trans)s/success" % FRONT_ROOT_URI
PAYMENT_PAYBOX_FAILURE = "%s/paybox/%%(id_trans)s/failure" % FRONT_ROOT_URI
PAYMENT_PAYBOX_CANCEL = "%s/paybox/%%(id_trans)s/cancel" % FRONT_ROOT_URI
PAYMENT_PAYBOX_WAITING = "%s/paybox/%%(id_trans)s/waiting" % FRONT_ROOT_URI
PAYMENT_PAYBOX_GATEWAY = "%s/payment/paybox/%%(id_trans)s/gateway" % USR_ROOT_URI


PAYPAL_SERVER = "https://www.sandbox.paypal.com/cgi-bin/webscr"

FIN_PAYMENT_NOTIFY_URL = {
    PAYMENT_TYPES.PAYPAL: '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI,
    PAYMENT_TYPES.PAYBOX: '%s/webservice/1.0/pub/paybox/trans/%%(id_trans)s' % FIN_ROOT_URI,
}

FIN_PAYPAL_TRANS = '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI
SELLER_EMAIL = 'business@infinite-code.com'

CURRENCY_EX_RATE = {
    'EUR': {'EUR': 1.0,
            'USD': 1.38251},

    'USD': {'USD': 1.0,
            'EUR': 0.72332}
}

LOCALE_LANGUAGES = ['zh', 'en', 'fr']
DEFAULT_LANGUAGE = 'en'

