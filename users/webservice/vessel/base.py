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


import settings
import logging
import os
import ujson
import urllib

from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SUtils.errors import ValidationError
from common.utils import api_key_verify
from common.utils import cookie_verify
from webservice.base import BaseJsonResource


def get_from_vessel_server(method, path, **query):
    remote_uri = os.path.join(settings.VSL_ROOT_URI, path)
    if query:
        query_str = urllib.urlencode(query)
        if method == 'GET':
            remote_uri = '?'.join([remote_uri, query_str])
            data = None
        else:
            data = gen_encrypt_json_context(
                query_str,
                settings.SERVER_APIKEY_URI_MAP['VSL'],
                settings.PRIVATE_KEY_PATH)

    try:
        content = get_from_remote(remote_uri,
                                  settings.SERVER_APIKEY_URI_MAP['VSL'],
                                  settings.PRIVATE_KEY_PATH,
                                  data=data)
    except Exception, e:
        logging.error('get_from_vessel_server: %s', e, exc_info=True)
        raise
    return ujson.loads(content)


class BaseVesselResource(BaseJsonResource):
    api_path = ''

    def _auth(self, conn, req, resp, **kwargs):
        try:
            if req.get_param('email') and req.get_param('api_key'):
                self.users_id = api_key_verify(conn,
                                               req.get_param('email'),
                                               req.get_param('api_key'))
            else:
                self.users_id = cookie_verify(conn, req, resp)

        except ValidationError, e:
            raise ValidationError('USER_AUTH_ERR')

    def _get_valid_args(self, req, resp, conn, **kwargs):
        raise NotImplementedError()

    def _on_get(self, req, resp, conn, **kwargs):
        remote_kwargs = self._get_valid_args(req, resp, conn, **kwargs)
        return get_from_vessel_server(req.method, self.api_path,
                                      **remote_kwargs)

    def _on_post(self, req, resp, conn, **kwargs):
        remote_kwargs = self._get_valid_args(req, resp, conn, **kwargs)
        return get_from_vessel_server(req.method, self.api_path,
                                      **remote_kwargs)

