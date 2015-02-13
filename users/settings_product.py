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


# users.backtoshops.com settings
from settings_base import *

PRODUCTION = True
LOG_CONFIG_FILE = 'product_logging.cfg'

ADM_ROOT_URI = "http://37.187.48.33"
USR_ROOT_URI = "http://92.222.30.2"
FIN_ROOT_URI = "http://92.222.30.3"
FRONT_ROOT_URI = "http://92.222.30.5"
VSL_ROOT_URI = "http://92.222.30.6"

SALES_SERVER_API_URL = "%s/webservice/1.0/%%(api)s" % ADM_ROOT_URI
FRONT_RESET_PASSWORD_URL = "%s/reset_password" % FRONT_ROOT_URI

SERVER_APIKEY_URI_MAP = {
    'USR': '%s/webservice/1.0/pub/apikey.pem' % USR_ROOT_URI,
    'ADM': '%s/webservice/1.0/pub/apikey.pem' % ADM_ROOT_URI,
    'FIN': '%s/webservice/1.0/pub/apikey.pem' % FIN_ROOT_URI,
    'VSL': '%s/webservice/1.0/pub/apikey.pem' % VSL_ROOT_URI,
    'FRO': '%s/webservice/1.0/pub/apikey.pem' % FRONT_ROOT_URI,
}


PAYMENT_PAYPAL_GATEWAY = "%s/payment/%%(id_trans)s/gateway" % USR_ROOT_URI
PAYMENT_PAYPAL_RETURN = "%s/payment/%%(id_trans)s/process" % USR_ROOT_URI
PAYMENT_PAYPAL_CANCEL = "%s/paypal/%%(id_trans)s/cancel" % FRONT_ROOT_URI

PAYMENT_PAYBOX_SUCCESS = "%s/paybox/%%(id_trans)s/success" % FRONT_ROOT_URI
PAYMENT_PAYBOX_FAILURE = "%s/paybox/%%(id_trans)s/failure" % FRONT_ROOT_URI
PAYMENT_PAYBOX_CANCEL = "%s/paybox/%%(id_trans)s/cancel" % FRONT_ROOT_URI
PAYMENT_PAYBOX_WAITING = "%s/paybox/%%(id_trans)s/waiting" % FRONT_ROOT_URI
PAYMENT_PAYBOX_GATEWAY = "%s/payment/paybox/%%(id_trans)s/gateway" % USR_ROOT_URI

PAYPAL_SERVER = "https://www.sandbox.paypal.com/cgi-bin/webscr"

FIN_PAYMENT_NOTIFY_URL = {
    PAYMENT_TYPES.PAYPAL: '%s/webservice/1.0/pub/paypal/trans/%%(id_trans)s' % FIN_ROOT_URI,
    PAYMENT_TYPES.PAYBOX: '%s/webservice/1.0/pub/paybox/trans/%%(id_trans)s' % FIN_ROOT_URI,
}

SELLER_EMAIL = 'business@infinite-code.com'
CURRENCY_EX_RATE = {
    'EUR': {'EUR': 1.0,
            'USD': 1.38251},

    'USD': {'USD': 1.0,
            'EUR': 0.72332}
}

# TODO: uncommon this after go live
#PAYPAL_SERVER = "https://www.paypal.com/cgi-bin/webscr"

SEND_EMAILS = True
