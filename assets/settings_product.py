# assets server settings
from settings_local import *

PRODUCTION = True

LOG_CONFIG_FILE = 'product_logging.cfg'

STATIC_FILES_PATH = '/var/local/assets/assets_files'
ADM_ROOT_URI = "http://37.187.48.33"
SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
}
