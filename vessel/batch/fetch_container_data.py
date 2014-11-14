import gevent
import logging
import settings
from B2SUtils import db_utils
from common.constants import CONTAINER_STATUS
from common.email_utils import send_container_arrival_notif
from common.thirdparty.datasource import getContainerDs


class FetchContainerData(object):

    def run(self):
        with db_utils.get_conn() as conn:
            self.fetch(conn)
            gevent.spawn_later(settings.FETCH_CONTAINER_INTERVAL, self.run)

    def fetch(self, conn):
        containers = db_utils.query(conn,
                    "select distinct container from container_arrival_notif "
                    "where not done")

        for c in containers:
            num = c[0]
            try:
                container_info = getContainerDs().searchContainer(
                                 search_by='container', number=num)
                last_pod = container_info['ports']['last_pod']
                for shipment in container_info['shipment_cycle']:
                    if last_pod and shipment['status'] \
                            == CONTAINER_STATUS.DISCHARGED_AT_LAST_POD:
                        gevent.spawn(send_container_arrival_notif, num, last_pod)
                        break
            except Exception, e:
                logging.error('Server Error: %s', (e,), exc_info=True)
                conn.rollback()
            else:
                conn.commit()

            gevent.sleep(1)

