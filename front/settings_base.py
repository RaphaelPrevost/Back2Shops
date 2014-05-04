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


TEMPLATE_PATH = ['views/templates']
DEFAULT_TEMPLATE = 'default.html'

LOG_CONFIG_FILE = 'logging.cfg'

USR_ROOT_URI = "http://localhost:8100"


PP_SUCCESS = "http://188.165.192.57:9500/payment/%(id_trans)s/success"
PP_FAILURE = "http://188.165.192.57:9500/payment/%(id_trans)s/failure"

USER_PM_FORM_URL = '%s/webservice/1.0/pub/payment/form' % USR_ROOT_URI