import logging
from models.stats_log import get_bought_history
from webservice.sensor.base import SensorBaseResource

from B2SProtocol.constants import RESP_RESULT
from B2SUtils.db_utils import delete

class SensorBoughtHistoryResource(SensorBaseResource):
    template = "sensor_bought_history.xml"

    def _on_get(self, req, resp, conn, **kwargs):
        histories = get_bought_history(conn)
        return {'GET_R': {'objects': histories}}

    def _on_post(self, req, resp, conn, **kwargs):
        try:
            super(SensorBoughtHistoryResource, self)._on_post(req, resp, conn, **kwargs)
            id_list = req.get_param('id_list')

            if id_list:
                where = {'id__in': tuple(id_list)}
                delete(self.conn, 'bought_history', where=where)
            logging.info('bought_history_del: %s', id_list)
            return {'POST_R': {'res': RESP_RESULT.S}}
        except Exception, e:
            logging.error('bought_history_del_err: %s', e, exc_info=True)
            return {'POST_R': {'res': RESP_RESULT.F}}
