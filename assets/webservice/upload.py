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
import falcon
import ujson

import settings
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError


class Collection(BaseJsonResource):

    def _on_post(self, req, resp, **kwargs):
        filename = req.get_param('name', required=True)
        storage_path = os.path.join(settings.STATIC_FILES_PATH, filename)

        directory = os.path.dirname(storage_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        content = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                 settings.PRIVATE_KEY_PATH)
        with open(storage_path, 'wb') as _f:
            _f.write(content)

        resp.status = falcon.HTTP_201
        return {'res': RESP_RESULT.S,
                'location': filename}

    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps(data_dict),
                            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                            settings.PRIVATE_KEY_PATH)
        return resp

