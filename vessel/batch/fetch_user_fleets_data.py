import gevent
import logging
import settings
from B2SUtils import db_utils
from common.utils import query_vessel_details


class FetchUserFleetsData(object):

    def run(self):
        with db_utils.get_conn() as conn:
            self.fetch(conn)
            gevent.spawn_later(settings.FETCH_VESSEL_INTERVAL, self.run)

    def fetch(self, conn):
        fleets = db_utils.query(conn,
                    "select distinct imo, mmsi from user_fleet")
        for imo, mmsi in fleets:
            if imo:
                search_by = 'imo'
                q = imo
            elif mmsi:
                search_by = 'mmsi'
                q = mmsi
            else:
                continue

            try:
                query_vessel_details(conn, search_by, q,
                                     settings.FETCH_VESSEL_INTERVAL/2)
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                conn.rollback()
            else:
                conn.commit()


def start():
    FetchUserFleetsData().run()

