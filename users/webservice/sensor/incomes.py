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


import logging
from models.stats_log import get_incomes_log
from webservice.sensor.base import SensorBaseResource

from B2SProtocol.constants import RESP_RESULT
from B2SUtils.db_utils import select, delete

class SensorIncomesResource(SensorBaseResource):
    template = "sensor_incomes.xml"
    time_field = 'up_time'

    def _on_get(self, req, resp, conn, **kwargs):
        where = self._get_req_range(req)

        try:
            objects = get_incomes_log(conn, where)
            return {'GET_R': {'objects': objects}}
        except Exception, e:
            logging.error('incomes_log_get_err: %s', e, exc_info=True)
            raise

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            super(SensorIncomesResource, self)._on_post(req, resp, conn, **kwargs)
            order_list = req.get_param('order_list')

            if order_list:
                where = {'order_id__in': tuple(order_list)}
                delete(self.conn, 'incomes_log', where=where)
            logging.info('incomes_log_del: %s', order_list)
            return {'POST_R': {'res': RESP_RESULT.S}}
        except Exception, e:
            logging.error('incomes_log_del_err: %s', e, exc_info=True)
            return {'POST_R': {'res': RESP_RESULT.F}}
