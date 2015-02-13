# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


import settings
import gevent
import logging
from B2SUtils import db_utils
from B2SUtils.email_utils import send_email


def send_html_email(to, subject, content):
    if not settings.SEND_EMAILS:
        return
    send_email(settings.SERVICE_EMAIL, to, subject, content, settings)

def send_vessel_arrival_notif(detail_vessel_obj):
    logging.info("Sending vessel arrival notif for %s" % detail_vessel_obj.name)

    msg = "Vessel %s is arriving in %s" % (
            detail_vessel_obj.name,
            detail_vessel_obj.departure_portname
            or detail_vessel_obj.departure_locode)

    with db_utils.get_conn() as conn:
        notifs = db_utils.select(conn, "vessel_arrival_notif",
                                 columns=("id", "email"),
                                 where={'mmsi': str(detail_vessel_obj.mmsi),
                                        'done': False})
        for _id, _email in notifs:
            send_html_email(_email,
                            msg,
                            msg)
            db_utils.update(conn, "vessel_arrival_notif",
                            values={'done': True},
                            where={'id': _id})
            conn.commit()

def send_container_arrival_notif(container, last_pod):
    logging.info("Sending container arrival notif for %s" % container)

    with db_utils.get_conn() as conn:
        msg = "Container(%s) is arriving in %s" % (container, last_pod)
        notifs = db_utils.select(conn, "container_arrival_notif",
                columns=("id", "email"),
                where={'container': container,
                       'done': False})
        for _id, _email in notifs:
            send_html_email(_email,
                            msg,
                            msg)
            db_utils.update(conn, "container_arrival_notif",
                            values={'done': True},
                            where={'id': _id})
            conn.commit()

