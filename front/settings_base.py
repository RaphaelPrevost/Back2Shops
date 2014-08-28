# frontend settings
import os
from platform import node

PRODUCTION = False
RUNNING_TEST = False

SERVER_PORT = 9500
FRONT_ROOT_URI = 'http://%s:%s' % (node().split('.')[0], SERVER_PORT)

CENTRAL_REDIS = {
    'HOST': 'localhost',
    'PORT': 6379,
    'TEST_PORT': 6279
}

BRAND_ID = "1000001"
BRAND_NAME = "BREUER"

TEMPLATE_PATH = ['views/templates/breuer']
#TEMPLATE_PATH = ['views/templates/dragondollar', 'views/templates/breuer']
DEFAULT_TEMPLATE = 'default.html'

DEFAULT_LANG = 'fr'

STATIC_FILES_PATH = 'static'

LOG_CONFIG_FILE = 'logging.cfg'

USR_ROOT_URI = "http://localhost:8100"

SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
}

PRIVATE_KEY_PATH = 'static/keys/front_pri.key'
PUB_KEY_PATH = 'static/keys/front_pub.key'

PP_SUCCESS = "http://localhost:9500/paypal/%(id_trans)s/success"
PP_FAILURE = "http://localhost:9500/paypal/%(id_trans)s/failure"

PB_SUCCESS = "http://localhost:9500/paybox/%(id_trans)s/success"
PB_ERROR = "http://localhost:9500/paybox/%(id_trans)s/error"
PB_CANCEL = "http://localhost:9500/paybox/%(id_trans)s/cancel"
PB_WAITING = "http://localhost:9500/paybox/%(id_trans)s/waiting"

NUM_OF_RANDOM_SALES = 4

SEND_EMAILS = False
SERVICE_EMAIL = 'serviceclients@breuer.fr'
MAIL_HOST = 'smtp.gmail.com:587'
MAIL_FROM_USER = 'xxx'
MAIL_FROM_PASS = 'xxx'

ORDERS_COUNT_IN_MY_ACCOUNT = 5
ORDERS_COUNT_PER_PAGE = 10
