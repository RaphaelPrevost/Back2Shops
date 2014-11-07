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

