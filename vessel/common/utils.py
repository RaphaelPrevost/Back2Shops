import settings
import logging
import ujson

from B2SUtils import db_utils
from B2SUtils.errors import DatabaseError
from common.models import VesselDetailInfo
from common.thirdparty.datasource import getDs


VESSEL_FIELDS = [
    'vessel.name', 'imo', 'mmsi', 'cs', 'type',
    'country_isocode', 'country.printable_name', 'photos']
VESSEL_NAV_FIELDS = [
    'departure_portname', 'departure_locode', 'departure_time',
    'arrival_portname', 'arrival_locode', 'arrival_time', 'status']
VESSEL_POS_FILES = ['location', 'longitude', 'latitude', 'heading', 'time']

def query_vessel_details(conn, search_by, q):
    sql = """
        select %s
        from vessel
        join vessel_navigation
           on (vessel.id=vessel_navigation.id_vessel)
        join vessel_position
           on (vessel_navigation.id=vessel_position.id_vessel_navigation)
        left join country
           on (vessel.country_isocode=country.iso)
        where vessel.%s=%%s
          and vessel_position.time > now() - interval '%%s seconds'
        order by vessel_position.time desc limit 1
        """ % (','.join(VESSEL_FIELDS + VESSEL_NAV_FIELDS + VESSEL_POS_FILES),
               search_by)

    if search_by != 'name':
        detail = db_utils.query(conn, sql, (q, settings.FETCH_VESSEL_INTERVAL))
        if len(detail) > 0:
            detail_results = []
            for item in detail:
                detail_obj = init_vessel_detail_obj(item, [item[-5:]])
                detail_results.append(detail_obj.toDict())
            return detail_results

    detail_results = getDs().getVesselInfo(**{search_by: q})
    for d in detail_results:
        try:
            detail_obj = VesselDetailInfo(**d)
            _save_result(conn, detail_obj)
        except DatabaseError, e:
            conn.rollback()
            logging.error('Server DB Error: %s', (e,), exc_info=True)

    return detail_results

def _save_result(conn, detail_obj):
    vessels = db_utils.select(conn, "vessel",
                             columns=("id", ),
                             where={'mmsi': str(detail_obj.mmsi)},
                             limit=1)
    if len(vessels) > 0:
        id_vessel = vessels[0][0]
    else:
        vessel_values = {
            'name': detail_obj.name,
            'imo': detail_obj.imo,
            'mmsi': detail_obj.mmsi,
            'cs': detail_obj.cs,
            'type': detail_obj.type,
            'country_isocode': detail_obj.country_isocode,
            'photos': ujson.dumps(detail_obj.photos),
        }
        id_vessel = db_utils.insert(conn, "vessel",
                                  values=vessel_values, returning='id')[0]

    navi_values = {
        'id_vessel': id_vessel,
        'departure_portname': detail_obj.departure_portname,
        'departure_locode': detail_obj.departure_locode,
        'departure_time': detail_obj.departure_time,
        'arrival_portname': detail_obj.arrival_portname,
        'arrival_locode': detail_obj.arrival_locode,
        'arrival_time': detail_obj.arrival_time,
        'status': detail_obj.status,
    }
    id_navi = db_utils.insert(conn, "vessel_navigation",
                              values=navi_values, returning='id')[0]
    for pos in detail_obj.positions:
        pos_values = {
            'id_vessel_navigation': id_navi,
            'location': pos.location,
            'longitude': pos.longitude,
            'latitude': pos.latitude,
            'heading': pos.heading,
            'time': pos.time,
        }
        db_utils.insert(conn, "vessel_position", values=pos_values)


def init_vessel_detail_obj(item, pos_list):
    positions = [dict(zip(VESSEL_POS_FILES, pos)) for pos in pos_list]
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
        status=item[14],
        positions=positions,
    )
    return detail_obj

