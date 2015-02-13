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
import gevent
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from common import cache
from B2SProtocol.constants import RESP_RESULT
from webservice.base import BaseJsonResource

class InvalidationResource(BaseJsonResource):

    def on_post(self, req, resp, **kwargs):
        try:
            data = decrypt_json_resp(req.stream,
                                settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                settings.PRIVATE_KEY_PATH)
            logging.info("Received cache invalidation %s" % data)
            method, obj_name, obj_id = data.split('/')
        except Exception, e:
            logging.error("Got exceptions when decrypting invalidation data",
                          exc_info=True)
            self.gen_resp(resp, {'res': RESP_RESULT.F})
        else:
            self.gen_resp(resp, {'res': RESP_RESULT.S})
            gevent.spawn_later(5, refresh_cache, method, obj_name, obj_id)


    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps(data_dict),
                            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                            settings.PRIVATE_KEY_PATH)
        return resp


def refresh_cache(method, obj_name, obj_id):
    proxy = getattr(cache, '%s_cache_proxy' % obj_name, None)
    if proxy is None:
        logging.error("No cache_proxy object for %s" % obj_name)
        return

    if method == 'DELETE':
        proxy.del_obj(obj_id)
    else:
        proxy.refresh(obj_id)

    proxy.cached_query_invalidate(obj_id, method)

