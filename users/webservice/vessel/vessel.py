from B2SUtils.errors import ValidationError
from webservice.vessel.base import BaseVesselResource


class VesselDetailResource(BaseVesselResource):
    api_path = 'webservice/1.0/protected/vessel/details'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        search_by = req.get_param('search_by')
        q = req.get_param('q')
        if search_by not in ('name', 'imo', 'mmsi', 'cs') or not q:
            raise ValidationError('INVALID_REQUEST')

        return {"search_by": search_by, "q": q}


class VesselNaviPathResource(BaseVesselResource):
    api_path = 'webservice/1.0/protected/vessel/path'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if not imo and not mmsi:
            raise ValidationError('INVALID_REQUEST')

        return {"mmsi": mmsi, "imo": imo}

