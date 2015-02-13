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


import falcon
import logging
import time
from datetime import datetime

from B2SProtocol.constants import RESP_RESULT
from B2SRespUtils.generate import gen_json_resp
from B2SUtils.errors import ValidationError


class BaseResource(object):
    request = None
    response = None

    def on_get(self, req, resp, **kwargs):
        self.request = req
        self.response = resp
        self._msg_handler('get', req, resp, **kwargs)

    def on_post(self, req, resp, **kwargs):
        self.request = req
        self.response = resp
        self._msg_handler('post', req, resp, **kwargs)

    def _msg_handler(self, method_name, req, resp, **kwargs):
        start_time = time.time() * 1000
        params = req._params
        logging.info('Got %s requet at %s UTC, %s with params %s'
                     % (req.method, datetime.utcnow(),
                        req.path, params))

        data = self.msg_handler(method_name, req, resp, **kwargs)
        self.gen_resp(resp, data)

        end_time = time.time() * 1000
        logging.info('Response %s Request: %s params: %s, in %s ms'
                     % (req.method, req.path, params,
                        end_time - start_time))

    def msg_handler(self, method_name, req, resp, **kwargs):
        try:
            method = getattr(self, '_on_' + method_name)
            data = method(req, resp, **kwargs)
        except ValidationError, e:
            logging.error('Validation Error: %s', (e,), exc_info=True)
            data = {'res': RESP_RESULT.F,
                    'err': str(e)}
        except Exception, e:
            logging.error('Server Error: %s', (e,), exc_info=True)
            data = {'res': RESP_RESULT.F,
                    'err': 'SERVER_ERR'}
        return data

    def _on_get(self, req, resp, **kwargs):
        return {}

    def _on_post(self, req, resp, **kwargs):
        return {}

    def gen_resp(self, resp, data):
        raise NotImplementedError


class BaseJsonResource(BaseResource):
    def gen_resp(self, resp, data):
        return gen_json_resp(resp, data)

