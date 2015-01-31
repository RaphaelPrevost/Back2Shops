# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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
import logging
import ujson
import urllib2
from django.core.files.storage import Storage

import settings
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SProtocol.constants import RESP_RESULT


def get_full_url(asset_name):
    return os.path.join(settings.ASSETS_CDN, asset_name)

def get_asset_name(full_url):
    return full_url.lstrip(settings.ASSETS_CDN)

def upload(asset_name, content):
    remote_uri = os.path.join(settings.AST_SERVER,
                              "webservice/1.0/private/upload?name=%s"
                              % urllib2.quote(asset_name))
    try:
        data = gen_encrypt_json_context(
            content.read(),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.AST],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            remote_uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.AST],
            settings.PRIVATE_KEY_PATH,
            data=data)
        return ujson.loads(resp)
    except Exception, e:
        logging.error("Failed to upload %s" % asset_name,
                      exc_info=True)
        raise


class AssetsStorage(Storage):
    def _open(self, name, mode='rb'):
        return urllib2.urlopen(self.url(name))

    def _save(self, name, content):
        result = upload(name, content)
        if result.get('res') == RESP_RESULT.F:
            raise Exception(result['err'])
        return result['location']

    def exists(self, name):
        try:
            self._open(name)
        except Exception:
            return False
        return True

    def listdir(self, path):
        pass

    def size(self, name):
        return 0

    def url(self, name):
        return get_full_url(name)

