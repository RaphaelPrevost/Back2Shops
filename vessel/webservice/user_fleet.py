import settings
import cgi
from StringIO import StringIO

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.base import BaseJsonResource
from common.utils import query_vessel_details


class UserFleetResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        id_user = req.get_param('id_user')
        if not id_user:
            raise ValidationError('INVALID_REQUEST')

        user_fleets = db_utils.select(conn, "user_fleet",
                                      columns=("imo", "mmsi"),
                                      where={'id_user': id_user})
        results = []
        for fleet in user_fleets:
            if fleet['imo']:
                search_by = 'imo'
                q = fleet['imo']
            else:
                search_by = 'mmsi'
                q = fleet['mmsi']

            details = query_vessel_details(conn, search_by, q)
            if len(details) > 0:
                results.append(details[0])

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
        imo = form_params.get('imo')
        mmsi = form_params.get('mmsi')

        if action not in ('add', 'delete'):
            raise ValidationError('INVALID_REQUEST')
        if not id_user or not imo or not mmsi:
            raise ValidationError('INVALID_REQUEST')

        values = {
            'id_user': id_user,
            'imo': imo,
            'mmsi': mmsi,
        }
        if action == 'add':
            user_fleet = db_utils.select(conn, "user_fleet",
                                         columns=("imo", "mmsi"),
                                         where={'id_user': id_user,
                                                'imo': imo,
                                                'mmsi': mmsi})
            if len(user_fleet) == 0:
                db_utils.insert(conn, "user_fleet", values=values)

        elif action == 'delete':
            db_utils.delete(conn, "user_fleet", where=values)

        return {'res': RESP_RESULT.S}

