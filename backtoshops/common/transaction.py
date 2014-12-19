# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


import os
import settings
import logging

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote

def remote_payment_init(data):
    uri = "webservice/1.0/private/payment/init"
    remote_uri = os.path.join(settings.FIN_SERVER, uri)
    try:
        data = gen_encrypt_json_context(
            data,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.FIN],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            remote_uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.FIN],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return resp
    except Exception, e:
        logging.error("Failed to send shipping fee %s" % data,
                      exc_info=True)
        raise
