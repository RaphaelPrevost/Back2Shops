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
