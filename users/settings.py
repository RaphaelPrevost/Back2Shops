# users.backtoshops.com settings

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
}
SALES_SERVER_API_URL = "http://localhost:8000/webservice/1.0/%(api)s"


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

SERVER_APIKEY_URI_MAP = {
    'USR': 'http://localhost:8100/webservice/1.0/pub/apikey.pem',
    'ADM': '%s/webservice/1.0/pub/apikey.pem' % ADM_ROOT_URI
}

PRIVATE_KEY_PATH = 'static/keys/usr_pri.key'
PUB_KEY_PATH = 'static/keys/usr_pub.key'

STATIC_ORDERS_IMG_PATH = 'static/orders_img/'

