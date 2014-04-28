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

STATIC_FILES_PATH = 'static'

LOG_CONFIG_FILE = 'logging.cfg'

USR_ROOT_URI = "http://localhost:8100"

