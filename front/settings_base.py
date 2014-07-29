# frontend settings
import os

PRODUCTION = False
RUNNING_TEST = False

SERVER_PORT = 9500

CENTRAL_REDIS = {
    'HOST': 'localhost',
    'PORT': 6379,
    'TEST_PORT': 6279
}


TEMPLATE_PATH = ['views/templates/breuer', 'views/templates/dragondollar']
#TEMPLATE_PATH = ['views/templates/dragondollar']
DEFAULT_TEMPLATE = 'default.html'

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

BRAND_ID = "1000001"
BRAND_NAME = "BREUER"

NUM_OF_RANDOM_SALES = 4
