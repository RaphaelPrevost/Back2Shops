# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


# finance.backtoshops.com settings
import os


SERVER_PORT = 9000 # for development only

DATABASE = {
    'NAME': 'finance',
    'USER': 'postgres',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '5432',
    'MAX_CONN': 50,
    'CONN_EXPIRATION': 1, #minute
}

LOG_CONFIG_FILE = 'logging.cfg'

USR_ROOT_URI = "http://localhost:8100"
ADM_ROOT_URI = "http://localhost:8000"

SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
    'ADM': os.path.join(ADM_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem')
}

PRIVATE_KEY_PATH = 'static/keys/finance_pri.key'
PUB_KEY_PATH = 'static/keys/finance_pub.key'

CRYPTO_RESP_DEBUGING = False

# need override in settings_local and settings_product
SELLER_EMAIL = None

B2S_TIMEZONE = 'Europe/Paris'

### Paybox
PAYBOX_REQUEST_URL = None
PAYBOX_SITE = None
PAYBOX_RANG = None
PAYBOX_IDENTIFIANT = None

PAYBOX_HASH_TYPE = 'SHA512'
PAYBOX_HMAC_KEY = None

### Stripe
STRIPE_API_KEY = None
