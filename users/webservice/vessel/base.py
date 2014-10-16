import settings
import logging
import os
import ujson
import urllib

from B2SCrypto.utils import get_from_remote
from B2SUtils.errors import ValidationError
from common.utils import api_key_verify
from common.utils import cookie_verify
from webservice.base import BaseJsonResource


def get_from_vessel_server(path, **query):
    remote_uri = os.path.join(settings.VSL_ROOT_URI, path)
    if query:
        query_str = urllib.urlencode(query)
        remote_uri = '?'.join([remote_uri, query_str])

    try:
        content = get_from_remote(remote_uri,
                                  settings.SERVER_APIKEY_URI_MAP['VSL'],
                                  settings.PRIVATE_KEY_PATH)
    except Exception, e:
        logging.error('get_from_vessel_server: %s', e, exc_info=True)
        raise
    return ujson.loads(content)


class BaseVesselResource(BaseJsonResource):
    login_required = {'get': True, 'post': True}
    api_path = ''

    def _auth(self, conn, req, resp, **kwargs):
        try:
            if req.get_param('email') and req.get_param('api_key'):
                self.users_id = api_key_verify(conn,
                                               req.get_param('email'),
                                               req.get_param('api_key'))
            else:
                self.users_id = cookie_verify(conn, req, resp)

        except ValidationError, e:
            raise ValidationError('USER_AUTH_ERR')

    def _get_valid_args(self, req, resp, conn, **kwargs):
        raise NotImplementedError()

    def _on_get(self, req, resp, conn, **kwargs):
        remote_kwargs = self._get_valid_args(req, resp, conn, **kwargs)
        return get_from_vessel_server(self.api_path, **remote_kwargs)

