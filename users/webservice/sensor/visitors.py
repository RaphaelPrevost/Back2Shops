import logging
from webservice.sensor.base import SensorBaseResource

from B2SProtocol.constants import RESP_RESULT
from B2SUtils.db_utils import select, delete

class SensorVisitorsResource(SensorBaseResource):
    template = "sensor_visitors.xml"

    def _on_get(self, req, resp, conn, **kwargs):
        where = self._get_req_range(req)
        r = select(self.conn, 'visitors_log', where=where)
        visitors = []
        for visitor in r:
            visitors.append(dict(visitor))

        data = {'number': len(visitors),
                'visitors': visitors}
        return {'GET': data}

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            super(SensorVisitorsResource, self)._on_post(req, resp, conn, **kwargs)
            sid_list = req.get_param('sid_list')

            if sid_list:
                where = {'sid__in': tuple(sid_list)}
                delete(self.conn, 'visitors_log', where=where)
            logging.info('visitors_log_del: %s', sid_list)
            return {'POST': {'res': RESP_RESULT.S}}
        except Exception, e:
            logging.error('visitors_log_del_err: %s', e, exc_info=True)
            return {'res': RESP_RESULT.F}
