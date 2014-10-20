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
