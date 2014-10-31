import settings
import cgi
from StringIO import StringIO

from B2SProtocol.constants import RESP_RESULT
from B2SUtils import db_utils
from B2SUtils.errors import ValidationError
from webservice.base import BaseJsonResource


CXV_FIELDS = ['container', 'bill_of_landing', 'first_pol', 'last_pod',
              'vessel_name', 'voyage']

class ContainerVesselResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        cxv = db_utils.select(conn, "container_x_vessel",
                              columns=['id'] + CXV_FIELDS,
                              where={'id_user': id_user})
        results = [dict(zip(['id'] + CXV_FIELDS, one)) for one in cxv]
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
        id_cxv = form_params.get('id')
        values = dict([(k, v) for k, v in form_params.iteritems()
                       if k in CXV_FIELDS])
        if action not in ('add', 'delete', 'update'):
            raise ValidationError('INVALID_REQUEST')
        if action in ('delete', 'update') and not id_cxv:
            raise ValidationError('INVALID_REQUEST')

        if action == 'add':
            db_utils.insert(conn, "container_x_vessel", values=values)
        elif action == 'update':
            db_utils.update(conn, "container_x_vessel", values=values,
                            where={'id': id_cxv})
        elif action == 'delete':
            db_utils.delete(conn, "container_x_vessel",
                            where={'id': id_cxv})

        return {'res': RESP_RESULT.S}
