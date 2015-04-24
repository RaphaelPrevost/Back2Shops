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


import os
import falcon
import itertools
import ujson

import settings
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError


class Collection(BaseJsonResource):
    service = SERVICES.ADM

    def _on_post(self, req, resp, **kwargs):
        rel_path = req.get_param('name', required=True)
        storage_path = os.path.join(settings.STATIC_FILES_PATH, rel_path)
        storage_path = self.get_available_name(storage_path)
        dir_name, file_name = os.path.split(storage_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        content = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[self.service],
                                 settings.PRIVATE_KEY_PATH)
        with open(storage_path, 'wb') as _f:
            _f.write(content)

        resp.status = falcon.HTTP_201
        new_rel_path = "%s/%s" % (os.path.dirname(rel_path), file_name)
        return {'res': RESP_RESULT.S,
                'location': new_rel_path}

    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps(data_dict),
                            settings.SERVER_APIKEY_URI_MAP[self.service],
                            settings.PRIVATE_KEY_PATH)
        return resp

    def get_available_name(self, name):
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        count = itertools.count(1)
        while os.path.exists(name):
            # file_ext includes the dot.
            name = os.path.join(dir_name, "%s_%s%s" % (file_root, count.next(), file_ext))
        return name


class AttachmentCollection(Collection):
    service = SERVICES.USR

