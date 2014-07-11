# users.backtoshops.com settings
import os
from common.constants import HASH_ALGORITHM

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
FRONT_ROOT_URI = "http://localhost:9500" # for testing only

SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FIN': os.path.join(FIN_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FRO': os.path.join(FRONT_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
}


PRIVATE_KEY_PATH = 'static/keys/usr_pri.key'
PUB_KEY_PATH = 'static/keys/usr_pub.key'

ORDERS_QUERY_LIMIT = 100
RUNNING_TEST = False

# config to see decrypt content for response,
# only used for debugging
CRYPTO_RESP_DEBUGING = True

PRODUCTION = False

INVOICE_VALIDATE_PATH = 'files/invoice/invoice.dtd'
INVOICE_XSLT_PATH = 'files/invoice/invoice.xsl'
SALES_VALIDATE_PATH = 'files/sales/sales.dtd'
SALEINFO_VALIDATE_PATH = 'files/sales/sale_info.dtd'
SHOPS_VALIDATE_PATH = 'files/shops/shops.dtd'
SHOPINFO_VALIDATE_PATH = 'files/shops/shop_info.dtd'

MAIL_HOST = 'smtp.gmail.com:587'
MAIL_FROM_USER = 'xxx'
MAIL_FROM_PASS = 'xxx'
MAIL_POSTFIX = 'gmail.com'



PAYMENT_GATEWAY = "%s/payment/%%(id_trans)s/gateway" % USR_ROOT_URI
PAYMENT_RETURN = "%s/payment/%%(id_trans)s/process" % USR_ROOT_URI
PAYMENT_CANCEL = "%s/payment/%%(id_trans)s/cancel" % FRONT_ROOT_URI

FRONT_PAYMENT_SUCCESS = "%s/paypal/%%(id_trans)s/success" % FRONT_ROOT_URI
FRONT_PAYMENT_FAILURE = "%s/paypal/%%(id_trans)s/failure" % FRONT_ROOT_URI

PAYPAL_SERVER = "https://www.sandbox.paypal.com/cgi-bin/webscr"

FIN_PAYPAL_TRANS = '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI
SELLER_EMAIL = 'business@infinite-code.com'

CURRENCY_EX_RATE = {
    'EUR': {'EUR': 1.0,
            'USD': 1.38251},

    'USD': {'USD': 1.0,
            'EUR': 0.72332}
}
