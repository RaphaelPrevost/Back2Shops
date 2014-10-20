from B2SUtils.errors import ValidationError
from webservice.vessel.base import BaseVesselResource


class SearchVesselResource(BaseVesselResource):
    api_path = 'webservice/1.0/protected/vessel/search'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'imo', 'mmsi', 'cs') or not q:
            raise ValidationError('INVALID_REQUEST')

        return {"search_by": search_by, "q": q,
                "details": req.get_param('details')}

class SearchPortResource(BaseVesselResource):
    api_path = 'webservice/1.0/protected/port/search'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'locode') or not q:
            raise ValidationError('INVALID_REQUEST')

        return {"search_by": search_by,
                "q": q,
                'country': req.get_param('country')}

