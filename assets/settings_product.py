# assets server settings
from settings_local import *

PRODUCTION = True

ADM_ROOT_URI = "http://188.165.192.57"
SERVER_APIKEY_URI_MAP = {
    'ADM': os.path.join(ADM_ROOT_URI, 'webservice/1.0/pub/apikey.pem'),
}
