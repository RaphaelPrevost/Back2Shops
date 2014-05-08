# assets server settings
import os

PRODUCTION = False
RUNNING_TEST = False

SERVER_PORT = 9300

STATIC_FILES_PATH = 'static'
PRIVATE_KEY_PATH = 'static/keys/ast_pri.key'
PUB_KEY_PATH = 'static/keys/ast_pub.key'

ADM_ROOT_URI = "http://localhost:8000"
SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
}

LOG_CONFIG_FILE = 'logging.cfg'

