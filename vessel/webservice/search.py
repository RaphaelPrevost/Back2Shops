import settings

from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from common.thirdparty.datasource import getContainerDs
from common.thirdparty.datasource import getVesselDs
from webservice.base import BaseJsonResource
from common.utils import query_vessel_details


class SearchVesselResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'imo', 'mmsi', 'cs') or not q:
            raise ValidationError('INVALID_REQUEST')

        if search_by == 'cs':
            search_by = 'name'
            # TODO: find according name in DB

        results = getVesselDs().searchVessel(**{search_by: q})

        if len(results) > 0 and req.get_param('details') == 'true':
            results = query_vessel_details(conn, search_by, q)

        return {'objects': results,
                'res': RESP_RESULT.S}


class SearchPortResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'locode') or not q:
            raise ValidationError('INVALID_REQUEST')

        results = getVesselDs().searchPort(**{search_by: q,
                                     'country': req.get_param('country')})
        return {'objects': results,
                'res': RESP_RESULT.S}


class SearchContainerResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('container', 'bill_of_landing') or not q:
            raise ValidationError('INVALID_REQUEST')

        results = []
        found, vessel_name, first_pol, last_pod = self._find_vessel(conn, search_by, q)
        if found:
            container_info = self._get_container_info(search_by, q,
                                  vessel_name, first_pol, last_pod)
            if container_info:
                if len(container_info['shipment_cycle']) > 0:
                    container_info['vessel_name'] = vessel_name
                    container_info['first_pol'] = first_pol
                    container_info['last_pod'] = last_pod

                    if container_info['shipment_cycle'][0]['mode'] == 'Vessel':
                        vessel_info = self._get_vessel_info(conn, vessel_name)
                        container_info['vessel_info'] = vessel_info
                results.append(container_info)
        return {'objects': results,
                'res': RESP_RESULT.S}

    def _find_vessel(self, conn, search_by, q):
        vessels = db_utils.select(conn, "container_x_vessel",
                columns=("vessel_name", "first_pol", "last_pod"),
                where={search_by: q},
                limit=1)
        if len(vessels) > 0:
            vessel_name, first_pol, last_pod = vessels[0]
            return True, vessel_name, first_pol, last_pod
        return False, None, None, None

    def _get_vessel_info(self, conn, vessel_name):
        vessel_info = None
        results = query_vessel_details(conn, 'name', vessel_name)
        for v in results:
            if settings.USE_MOCK_FLEETMON_DATA or v['name'] == vessel_name:
                vessel_info = v
                break
        return vessel_info

    def _get_container_info(self, search_by, q,
                            vessel_name, first_pol, last_pod):
        container_info = getContainerDs().searchContainer(
                            search_by=search_by, number=q)
        return container_info

