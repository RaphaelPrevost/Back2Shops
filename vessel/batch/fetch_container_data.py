# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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

