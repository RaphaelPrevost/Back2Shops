import settings
import datetime
import logging
import ujson

from B2SUtils import db_utils
from B2SUtils.common import localize_datetime
from B2SUtils.common import parse_ts
from B2SUtils.errors import DatabaseError
from common.constants import VESSEL_STATUS
from common.email_utils import send_vessel_arrival_notif
from common.models import VesselDetailInfo
from common.thirdparty.datasource import getVesselDs


VESSEL_FIELDS = [
    'vessel.name', 'imo', 'mmsi', 'cs', 'type',
    'country_isocode', 'country.printable_name', 'photos']
VESSEL_NAV_FIELDS = [
    'departure_locode', 'departure_time', 'arrival_locode', 'arrival_time']
VESSEL_POS_FIELDS = ['location', 'longitude', 'latitude', 'heading',
                     'speed', 'status', 'time']


def query_vessel_details(conn, search_by, q,
                         force=False, exact_match=False):
    fields = VESSEL_FIELDS + VESSEL_NAV_FIELDS + VESSEL_POS_FIELDS
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
        """ % (','.join(fields), search_by)

    if not force and (search_by != 'name' or exact_match):
        detail = db_utils.query(conn, sql, (q, ))
        if len(detail) > 0 and \
                not need_fetch_new_pos(dict(zip(fields, detail[0]))['time']):
            detail_results = []
            for item in detail:
                item_dict = dict(zip(fields, item))
                detail_obj = init_vessel_detail_obj(item_dict, [item_dict])
                detail_obj.update_portnames(conn)
                detail_results.append(detail_obj.toDict())
            return detail_results

    records, old_records = getVesselDs().getVesselInfo(**{search_by: q})
    detail_results = []
    for d in records:
        try:
            detail_obj = VesselDetailInfo(**d)
            detail_obj.update_portnames(conn)
            _save_result(conn, detail_obj)

            update_interval = _get_update_interval(detail_obj)
            now = datetime.datetime.utcnow()
            delta = datetime.timedelta(seconds=update_interval)
            db_utils.update(conn, "vessel",
                            values={'next_update_time': now + delta},
                            where={'mmsi': str(detail_obj.mmsi)})

            detail_results.append(detail_obj.toDict())
        except DatabaseError, e:
            conn.rollback()
            logging.error('Server DB Error: %s', (e,), exc_info=True)
            detail_results.append(d)

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

        if pos.status.lower() == VESSEL_STATUS.MOORED:
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
            'departure_locode': detail_obj.departure_locode,
            'departure_time': parse_ts(detail_obj.departure_time),
            'arrival_locode': detail_obj.arrival_locode,
        }
        navi_update_values = {
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

def init_vessel_detail_obj(item_dict, positions):
    detail_obj = VesselDetailInfo(
        name=item_dict['vessel.name'],
        imo=item_dict['imo'],
        mmsi=item_dict['mmsi'],
        cs=item_dict['cs'],
        type=item_dict['type'],
        country_isocode=item_dict['country_isocode'],
        country_name=item_dict['country.printable_name'],
        photos=ujson.loads(item_dict['photos']),

        departure_portname=item_dict.get('departure_portname', ''),
        departure_locode=item_dict['departure_locode'],
        departure_time=item_dict['departure_time'],
        arrival_portname=item_dict.get('arrival_portname', ''),
        arrival_locode=item_dict['arrival_locode'],
        arrival_time=item_dict['arrival_time'],
        positions=positions,
    )
    return detail_obj

