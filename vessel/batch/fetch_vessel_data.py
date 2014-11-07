import datetime
import gevent
import logging
import settings
from B2SUtils import db_utils
from common.utils import query_vessel_details


class FetchVesselData(object):

    def run(self):
        with db_utils.get_conn() as conn:
            self.fetch(conn)
            gevent.spawn_later(settings.FETCH_VESSEL_MIN_INTERVAL, self.run)

    def fetch(self, conn):
        vessels = db_utils.query(conn,
                    "select distinct mmsi from vessel "
                    "where next_update_time <= %s",
                    (datetime.datetime.utcnow(), ))

        for v in vessels:
            mmsi = v[0]
            try:
                query_vessel_details(conn, 'mmsi', mmsi,
                                     force=True)
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                conn.rollback()
            else:
                conn.commit()

