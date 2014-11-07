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
        container_info = self._get_container_info(conn, search_by, q)
        if len(container_info['shipment_cycle']) > 0:
            results.append(container_info)
        return {'objects': results,
                'res': RESP_RESULT.S}

    def _get_vessel_info(self, conn, vessel_name):
        vessel_info = None
        results = query_vessel_details(conn, 'name', vessel_name)
        for v in results:
            if settings.USE_MOCK_FLEETMON_DATA or v['name'] == vessel_name:
                vessel_info = v
                break
        return vessel_info

    def _get_container_info(self, conn, search_by, q):
        container_info = getContainerDs().searchContainer(
                            search_by=search_by, number=q)
        for shipment in container_info['shipment_cycle']:
            if shipment['vessel_name']:
                vessel_info = self._get_vessel_info(conn, shipment['vessel_name'])
                container_info['vessel_info'] = vessel_info
            break
        return container_info

