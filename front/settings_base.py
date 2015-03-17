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
#TEMPLATE_PATH = ['views/templates/vessel', 'views/templates/breuer']
DEFAULT_TEMPLATE = 'default.html'

DEFAULT_LOCALE = 'fr_FR'
SUPPORTED_LOCALES = ['fr_FR']
LOCALE_DIR = '../locale'
LOCALE_DOMAIN = 'front'

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

SP_SUCCESS = "http://localhost:9500/stripe/%(id_trans)s/success"
SP_FAILURE = "http://localhost:9500/stripe/%(id_trans)s/failure"

NUM_OF_RANDOM_SALES = 4

SEND_EMAILS = False
SERVICE_EMAIL = 'serviceclients@breuer.fr'
MAIL_HOST = 'smtp.gmail.com:587'
MAIL_FROM_USER = 'xxx'
MAIL_FROM_PASS = 'xxx'

ORDERS_COUNT_IN_MY_ACCOUNT = 5
ORDERS_COUNT_PER_PAGE = 10

SESSION_EXP_TIME = 1800

TIMEZONE = 'Europe/Paris'


DRAGON_FEED_CACHE_PATH = None
