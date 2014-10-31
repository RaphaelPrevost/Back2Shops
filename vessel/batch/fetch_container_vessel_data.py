import gevent
import logging
import settings
from B2SUtils import db_utils
from common.utils import query_vessel_details


class FetchContainerVesselData(object):

    def run(self):
        with db_utils.get_conn() as conn:
            self.fetch(conn)
            gevent.spawn_later(settings.FETCH_VESSEL_INTERVAL, self.run)

    def fetch(self, conn):
        vessels = db_utils.query(conn,
                    "select distinct vessel_name from container_x_vessel")
        for name in vessels:
            search_by = 'name'
            q = name
            try:
                query_vessel_details(conn, search_by, q,
                                     settings.FETCH_VESSEL_INTERVAL/2)
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                conn.rollback()
            else:
                conn.commit()

