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

        fields = ['vessel.id'] + VESSEL_FIELDS + VESSEL_NAV_FIELDS
        sql = """
            select %s
            from vessel
            join vessel_navigation
               on (vessel.id=vessel_navigation.id_vessel)
            left join country
               on (vessel.country_isocode=country.iso)
            where vessel.%s=%%s
            order by created desc limit 1
            """ % (','.join(fields),
                   search_by)
        vessel_nav = db_utils.query(conn, sql, (q,))

        return_obj = {}
        if len(vessel_nav) > 0:
            vessel_nav = vessel_nav[0]
            vessel_nav_dict = dict(zip(fields, vessel_nav))
            id_vessel = vessel_nav_dict['vessel.id']
            sql = """
                select %s
                from vessel_position
                where id_vessel = %%s
                  and time >= %%s and time <= %%s
                order by time desc
                """ % ','.join(VESSEL_POS_FIELDS)
            positions = db_utils.query(conn, sql,
                               (id_vessel,
                                vessel_nav_dict['departure_time'],
                                vessel_nav_dict['arrival_time']))
            if positions:
                positions = [dict(zip(VESSEL_POS_FIELDS, pos))
                             for pos in positions]
                detail_obj = init_vessel_detail_obj(vessel_nav_dict, positions)
                detail_obj.update_portnames(conn)
                return_obj = detail_obj.toDict()

        return {'object': return_obj,
                'res': RESP_RESULT.S}

