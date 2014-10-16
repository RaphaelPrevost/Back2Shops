import settings
from webservice.base import BaseResource
from B2SCrypto.utils import get_key_from_local

class ApiKeyResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        key = get_key_from_local(settings.PUB_KEY_PATH)
        resp.body = key
        return resp

    def _on_post(self, req, resp, conn, **kwargs):
        return self._on_get(req, resp, conn, **kwargs)
