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


import logging
from models.stats_log import get_orders_log
from webservice.sensor.base import SensorBaseResource

from B2SProtocol.constants import RESP_RESULT
from B2SUtils.db_utils import delete

class SensorOrdersResource(SensorBaseResource):
    template = "sensor_orders.xml"
    time_field = 'up_time'

    def _on_get(self, req, resp, conn, **kwargs):
        where = self._get_req_range(req)
        logs = get_orders_log(conn, where['from_'], where['to'])
        return {'GET_R': {'objects': logs}}

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            super(SensorOrdersResource, self)._on_post(req, resp, conn, **kwargs)
            id_list = req.get_param('id_list')

            if id_list:
                where = {'id__in': tuple(id_list)}
                delete(self.conn, 'orders_log', where=where)
            logging.info('orders_log_del: %s', id_list)
            return {'POST_R': {'res': RESP_RESULT.S}}
        except Exception, e:
            logging.error('orders_log_del_err: %s', e, exc_info=True)
            return {'POST_R': {'res': RESP_RESULT.F}}

    def _get_req_range(self, req):
        return {'from_': req.get_param('from'),
                'to': req.get_param('to')}
