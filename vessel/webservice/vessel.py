from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.base import BaseJsonResource
from common.utils import query_vessel_details
from common.utils import init_vessel_detail_obj
from common.utils import VESSEL_FIELDS, VESSEL_NAV_FIELDS, VESSEL_POS_FIELDS


class VesselDetailResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'imo', 'mmsi', 'cs') or not q:
            raise ValidationError('INVALID_REQUEST')

        if search_by == 'cs':
            search_by = 'name'
            # TODO: find according name in DB

        return {'objects': query_vessel_details(conn, search_by, q),
                'res': RESP_RESULT.S}


class VesselNaviPathResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if not imo and not mmsi:
            raise ValidationError('INVALID_REQUEST')

        if imo:
            search_by = 'imo'
            q = imo
        else:
            search_by = 'mmsi'
            q = mmsi

        sql = """
            select vessel.id, %s
            from vessel
            join vessel_navigation
               on (vessel.id=vessel_navigation.id_vessel)
            left join country
               on (vessel.country_isocode=country.iso)
            where vessel.%s=%%s
            order by created desc limit 1
            """ % (','.join(VESSEL_FIELDS + VESSEL_NAV_FIELDS),
                   search_by)
        vessel_nav = db_utils.query(conn, sql, (q,))

        return_obj = {}
        if len(vessel_nav) > 0:
            vessel_nav = vessel_nav[0]
            id_vessel = vessel_nav.pop(0)
            sql = """
                select %s
                from vessel_position
                where id_vessel = %%s
                  and time >= %%s and time <= %%s
                order by time desc
                """ % ','.join(VESSEL_POS_FIELDS)
            positions = db_utils.query(conn, sql,
                               (id_vessel, vessel_nav[10], vessel_nav[13]))
            if positions:
                detail_obj = init_vessel_detail_obj(vessel_nav, positions)
                return_obj = detail_obj.toDict()

        return {'object': return_obj,
                'res': RESP_RESULT.S}

