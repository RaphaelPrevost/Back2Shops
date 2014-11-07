import settings
import cgi
from StringIO import StringIO

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.base import BaseJsonResource


class VesselArrivalNotif(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        id_user = req.get_param('id_user')
        if not id_user:
            raise ValidationError('INVALID_REQUEST')

        results = db_utils.select(conn, "vessel_arrival_notif",
                                  columns=("imo", "mmsi"),
                                  where={'id_user': id_user,
                                         'done': False})
        return {'objects': results,
                'res': RESP_RESULT.S}

    def _on_post(self, req, resp, conn, **kwargs):
        f = StringIO(req.query_string)
        data = decrypt_json_resp(f,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                                 settings.PRIVATE_KEY_PATH)
        f.close()

        form_params = cgi.parse_qs(data)
        for p in form_params:
            form_params[p] = form_params[p][0]
        action = form_params.get('action')
        id_user = form_params.get('id_user')
        email = form_params.get('email')
        imo = form_params.get('imo')
        mmsi = form_params.get('mmsi')

        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not id_user or not email or not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')

        values = {
            'id_user': id_user,
            'email': email,
            'imo': imo,
            'mmsi': mmsi,
            'done': False,
        }
        if action == 'add':
            records = db_utils.select(conn, "vessel_arrival_notif",
                                      columns=("imo", "mmsi"),
                                      where=values)
            if len(records) == 0:
                db_utils.insert(conn, "vessel_arrival_notif", values=values)

        elif action == 'delete':
            db_utils.delete(conn, "vessel_arrival_notif", where=values)

        return {'res': RESP_RESULT.S}


class ContainerArrivalNotif(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        id_user = req.get_param('id_user')
        if not id_user:
            raise ValidationError('INVALID_REQUEST')

        results = db_utils.select(conn, "container_arrival_notif",
                                  columns=("container", ),
                                  where={'id_user': id_user,
                                         'done': False})
        return {'objects': results,
                'res': RESP_RESULT.S}

    def _on_post(self, req, resp, conn, **kwargs):
        f = StringIO(req.query_string)
        data = decrypt_json_resp(f,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                                 settings.PRIVATE_KEY_PATH)
        f.close()

        form_params = cgi.parse_qs(data)
        for p in form_params:
            form_params[p] = form_params[p][0]
        action = form_params.get('action')
        id_user = form_params.get('id_user')
        email = form_params.get('email')
        container = form_params.get('container')

        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not id_user or not email or not container:
            raise ValidationError('INVALID_REQUEST')

        values = {
            'id_user': id_user,
            'email': email,
            'container': container,
            'done': False,
        }
        if action == 'add':
            records = db_utils.select(conn, "container_arrival_notif",
                                      columns=("container", ),
                                      where=values)
            if len(records) == 0:
                db_utils.insert(conn, "container_arrival_notif", values=values)

        elif action == 'delete':
            db_utils.delete(conn, "container_arrival_notif", where=values)

        return {'res': RESP_RESULT.S}

