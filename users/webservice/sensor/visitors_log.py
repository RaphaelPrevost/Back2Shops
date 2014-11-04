import logging
from webservice.base import BaseJsonResource

from B2SProtocol.constants import RESP_RESULT
from B2SUtils.db_utils import select, update, insert

class SensorVisitorsLogResource(BaseJsonResource):
    def _on_post(self, req, resp, conn, **kwargs):
        try:
            sid = req.get_param('sid')
            users_id = req.get_param('users_id') or None

            where = {'sid': sid}
            v_log = select(conn, 'visitors_log', where=where)
            if len(v_log) > 0:
                update(conn,
                       'visitors_log',
                       {'users_id': users_id},
                        where={'sid': sid})
            else:
                values = {'sid': sid,
                          'users_id': users_id}
                insert(conn, 'visitors_log', values=values)

            return {'result': RESP_RESULT.S }
        except Exception, e:
            logging.error('visitors_log_err: %s', e, exc_info=True)
            return {'result': RESP_RESULT.F}
