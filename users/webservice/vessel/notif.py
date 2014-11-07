from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.vessel.base import BaseVesselResource


class VesselArrivalNotifResource(BaseVesselResource):
    login_required = {'get': True, 'post': True}
    api_path = 'webservice/1.0/private/vessel/reminder'

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

        email = db_utils.select(conn, "users",
                    columns=('email',),
                    where={'id': self.users_id})[0][0]
        return {
            "action": action,
            "id_user": self.users_id,
            "email": email,
            "mmsi": mmsi,
            "imo": imo,
        }


class ContainerArrivalNotifResource(BaseVesselResource):
    login_required = {'get': True, 'post': True}
    api_path = 'webservice/1.0/private/container/reminder'

    def _get_valid_args(self, req, resp, conn, **kwargs):
        if req.method == 'GET':
            return {"id_user": self.users_id}

        action = req.get_param('action')
        container = req.get_param('container')
        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not container:
            raise ValidationError('INVALID_REQUEST')

        email = db_utils.select(conn, "users",
                    columns=('email',),
                    where={'id': self.users_id})[0][0]
        return {
            "action": action,
            "id_user": self.users_id,
            "email": email,
            "container": container,
        }

