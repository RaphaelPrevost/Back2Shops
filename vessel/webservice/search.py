from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError
from common.thirdparty.datasource import getDs
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

        results = getDs().searchVessel(**{search_by: q})

        if len(results) > 0 and req.get_param('details') == 'true':
            results = query_vessel_details(conn, search_by, q)

        return {'objects': results,
                'res': RESP_RESULT.S}


class SearchPortResource(BaseJsonResource):
    login_required = {'get': True, 'post': False}

    def _on_get(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'locode') or not q:
            raise ValidationError('INVALID_REQUEST')

        results = getDs().searchPort(**{search_by: q,
                                     'country': req.get_param('country')})
        return {'objects': results,
                'res': RESP_RESULT.S}
