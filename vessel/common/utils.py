import settings
import datetime
import logging
import ujson

from B2SUtils import db_utils
from B2SUtils.common import localize_datetime
from B2SUtils.common import parse_ts
from B2SUtils.errors import DatabaseError
from common.email_utils import send_vessel_arrival_notif
from common.models import VesselDetailInfo
from common.thirdparty.datasource import getVesselDs


VESSEL_FIELDS = [
    'vessel.name', 'imo', 'mmsi', 'cs', 'type',
    'country_isocode', 'country.printable_name', 'photos']
VESSEL_NAV_FIELDS = [
    'departure_portname', 'departure_locode', 'departure_time',
    'arrival_portname', 'arrival_locode', 'arrival_time']
VESSEL_POS_FIELDS = ['location', 'longitude', 'latitude', 'heading',
                     'speed', 'status', 'time']


def query_vessel_details(conn, search_by, q,
                         force=False, exact_match=False):
    sql = """
        select %s
        from vessel
        join vessel_navigation
           on (vessel.id=vessel_navigation.id_vessel)
        join vessel_position
           on (vessel.id=vessel_position.id_vessel)
        left join country
           on (vessel.country_isocode=country.iso)
        where vessel.%s=%%s
          and vessel_position.time >= vessel_navigation.departure_time
          and vessel_position.time <= vessel_navigation.arrival_time
        order by vessel_position.time desc limit 1
        """ % (','.join(VESSEL_FIELDS + VESSEL_NAV_FIELDS + VESSEL_POS_FIELDS),
               search_by)

    if not force and (search_by != 'name' or exact_match):
        detail = db_utils.query(conn, sql, (q, ))
        if len(detail) > 0 and not need_fetch_new_pos(detail[0][-1]):
            detail_results = []
            for item in detail:
                detail_obj = init_vessel_detail_obj(item, [item[-5:]])
                detail_results.append(detail_obj.toDict())
            return detail_results

    detail_results, old_records = getVesselDs().getVesselInfo(**{search_by: q})
    for d in detail_results:
        try:
            detail_obj = VesselDetailInfo(**d)
            _save_result(conn, detail_obj)

            update_interval = _get_update_interval(detail_obj)
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(seconds=update_interval)
            db_utils.update(conn, "vessel",
                            values={'next_update_time': now + delta},
                            where={'mmsi': str(detail_obj.mmsi)})
        except DatabaseError, e:
            conn.rollback()
            logging.error('Server DB Error: %s', (e,), exc_info=True)

    for d in old_records:
        try:
            detail_obj = VesselDetailInfo(**d)
            _save_result(conn, detail_obj, update_only=True)
        except DatabaseError, e:
            conn.rollback()
            logging.error('Server DB Error: %s', (e,), exc_info=True)

    return detail_results

def _get_update_interval(detail_obj):
    update_interval = settings.FETCH_VESSEL_MIN_INTERVAL
    if len(detail_obj.positions) > 0:
        pos = detail_obj.positions[0]
        # TODO: set update interval to 4h if vessel in distant sea
        update_interval = settings.FETCH_VESSEL_MAX_INTERVAL

        if pos.status.lower() == 'moored':
            gevent.spawn(send_vessel_arrival_notif, detail_obj)

    return update_interval

def need_fetch_new_pos(last_pos_time):
    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=settings.FETCH_VESSEL_MAX_INTERVAL)
    return last_pos_time < now - delta

def _save_result(conn, detail_obj, update_only=False):
    vessels = db_utils.select(conn, "vessel",
                             columns=("id", ),
                             where={'mmsi': str(detail_obj.mmsi)},
                             limit=1)
    vessel_values = {
        'name': detail_obj.name,
        'imo': detail_obj.imo,
        'mmsi': detail_obj.mmsi,
        'cs': detail_obj.cs,
        'type': detail_obj.type,
        'country_isocode': detail_obj.country_isocode,
        'photos': ujson.dumps(detail_obj.photos),
    }
    if len(vessels) > 0:
        id_vessel = vessels[0][0]
        db_utils.update(conn, "vessel", values=vessel_values,
                        where={'id': id_vessel})
    else:
        if update_only: return
        id_vessel = db_utils.insert(conn, "vessel",
                                  values=vessel_values, returning='id')[0]

    if detail_obj.departure_time and detail_obj.arrival_time:
        navi_values = {
            'id_vessel': id_vessel,
            'departure_portname': detail_obj.departure_portname,
            'departure_locode': detail_obj.departure_locode,
            'departure_time': parse_ts(detail_obj.departure_time),
            'arrival_locode': detail_obj.arrival_locode,
        }
        navi_update_values = {
            'arrival_portname': detail_obj.arrival_portname,
            'arrival_time': parse_ts(detail_obj.arrival_time),
        }
        vessel_nav = db_utils.select(conn, "vessel_navigation",
                                 columns=("id", ),
                                 where=navi_values,
                                 order=('arrival_time__desc', ),
                                 limit=1)
        if len(vessel_nav) > 0:
            id_navi = vessel_nav[0][0]
            db_utils.update(conn, "vessel_navigation",
                            values=navi_update_values,
                            where={'id': id_navi})

        else:
            if update_only: return
            navi_values.update(navi_update_values)
            id_navi = db_utils.insert(conn, "vessel_navigation",
                                      values=navi_values, returning='id')[0]

    if update_only: return

    for pos in detail_obj.positions:
        pos_values = {
            'id_vessel': id_vessel,
            'location': pos.location,
            'longitude': pos.longitude,
            'latitude': pos.latitude,
            'heading': pos.heading,
            'speed': pos.speed,
            'time': parse_ts(pos.time),
            'status': pos.status,
        }
        db_utils.insert(conn, "vessel_position", values=pos_values)

def format_datetime(dt_str, tz_from, tz_to):
    dt = parse_ts(dt_str)
    if dt is None:
        if dt_str:
            logging.error('Failed to format datetime: %s', dt_str)
        return dt_str
    return localize_datetime(dt, tz_from, tz_to
                             ).strftime('%Y-%m-%d %H:%M')

def init_vessel_detail_obj(item, pos_list):
    positions = [dict(zip(VESSEL_POS_FIELDS, pos)) for pos in pos_list]
    detail_obj = VesselDetailInfo(
        name=item[0],
        imo=item[1],
        mmsi=item[2],
        cs=item[3],
        type=item[4],
        country_isocode=item[5],
        country_name=item[6],
        photos=ujson.loads(item[7]),

        departure_portname=item[8],
        departure_locode=item[9],
        departure_time=item[10],
        arrival_portname=item[11],
        arrival_locode=item[12],
        arrival_time=item[13],
        positions=positions,
    )
    return detail_obj

