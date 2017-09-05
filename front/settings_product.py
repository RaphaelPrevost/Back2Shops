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
from settings_local import *

PRODUCTION = True
LOG_CONFIG_FILE = 'product_logging.cfg'

STATIC_FILES_PATH = '/var/local/assets/front_files'

USR_ROOT_URI = "http://92.222.30.2"

import urlparse
CENTRAL_REDIS = {
    'HOST': urlparse.urlparse(USR_ROOT_URI).hostname,
    'PORT': 6379,
    'TEST_PORT': 6279,
    'PASSWORD': 'setpassforsafety',
}

SERVER_APIKEY_URI_MAP = {
    'USR': os.path.join(USR_ROOT_URI,
                        'webservice/1.0/pub/apikey.pem'),
}

FRONT_ROOT_URI = "http://92.222.30.5"
PP_SUCCESS = "%s/paypal/%%(id_trans)s/success" % FRONT_ROOT_URI
PP_FAILURE = "%s/paypal/%%(id_trans)s/failure" % FRONT_ROOT_URI

PB_SUCCESS = "%s/paybox/%%(id_trans)s/success" % FRONT_ROOT_URI
PB_ERROR = "%s/paybox/%%(id_trans)s/error" % FRONT_ROOT_URI
PB_CANCEL = "%s/paybox/%%(id_trans)s/cancel" % FRONT_ROOT_URI
PB_WAITING = "%s/paybox/%%(id_trans)s/waiting" % FRONT_ROOT_URI

SP_SUCCESS = "%s/stripe/%%(id_trans)s/success" % FRONT_ROOT_URI
SP_FAILURE = "%s/stripe/%%(id_trans)s/failure" % FRONT_ROOT_URI

BRAND_ID = "1"

SEND_EMAILS = True
