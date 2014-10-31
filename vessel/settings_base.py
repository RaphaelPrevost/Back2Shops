import os

SERVER_PORT = 8700

DATABASE = {
    'NAME': 'vessel',
    'USER': 'postgres',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '5432',
    'MAX_CONN': 50,
    'CONN_EXPIRATION': 1, #minute
}

LOG_CONFIG_FILE = 'logging.cfg'

USR_ROOT_URI = "http://localhost:8100"
SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
}

PRIVATE_KEY_PATH = 'static/keys/vessel_pri.key'
PUB_KEY_PATH = 'static/keys/vessel_pub.key'


USE_FLEETMON = True
FLEETMON_API_URL = 'http://www.fleetmon.com'
FLEETMON_USERNAME = 'nereustechnology'
FLEETMON_API_KEY = 'e3651ac0347ca2a8370664ba060a586c72fa477b'
USE_MOCK_FLEETMON_DATA = True # mock generic vessel api which is billed per use

USE_COSCON_CONTAINER = True
COSCON_CONTAINER_URL = 'http://ebusiness.coscon.com/NewEBWeb/public/cargoTracking/cargoTracking.xhtml'

THIRDPARTY_ACCESS_TIMEOUT = 5

FETCH_VESSEL_INTERVAL = 3600 * 4 # seconds

