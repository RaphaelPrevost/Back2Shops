from B2SUtils.errors import ValidationError
from webservice.vessel.base import BaseVesselResource


class UserFleetResource(BaseVesselResource):
    login_required = {'get': True, 'post': True}
    api_path = 'webservice/1.0/private/user_fleet'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        if req.method == 'GET':
            return {"id_user": self.users_id}

        action = req.get_param('action')
        imo = req.get_param('imo')
        mmsi = req.get_param('mmsi')
        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')
        return {
            "action": action,
            "id_user": self.users_id,
            "mmsi": mmsi,
            "imo": imo,
        }

