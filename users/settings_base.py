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
    'MAX_CONN': 10,
    'CONN_EXPIRATION': 1, #minute
}
CENTRAL_REDIS = {
    'HOST': 'localhost',
    'PORT': 6379,
    'TEST_PORT': 6279
}


DEFAULT_PASSWORD_HASH_ALGORITHM = HASH_ALGORITHM.WHIRLPOOL
HASH_MIN_ITERATIONS = 2
HASH_MAX_ITERATIONS = 256
USER_CREATION_CAPTCHA = "1234" # temporary solution for now

USER_AUTH_COOKIE_NAME = 'USER_AUTH'
USER_AUTH_COOKIE_EXPIRES = 8 * 3600
USER_AUTH_COOKIE_DOMAIN = '.backtoshops.com'

SUPPORTED_MAJOR_COUNTRIES = ['US', 'CA', 'CN']

LOG_CONFIG_FILE = 'logging.cfg'

HMAC_KEY_SIZE = 128
HMAC_KEY_FILE_PATH = 'hmac.pem'

ADM_ROOT_URI = "http://localhost:8000"
FIN_ROOT_URI = "http://localhost:9000"
SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
    'FIN': os.path.join(FIN_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
}


PRIVATE_KEY_PATH = 'static/keys/usr_pri.key'
PUB_KEY_PATH = 'static/keys/usr_pub.key'

STATIC_ORDERS_IMG_PATH = 'static/orders_img/'

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
