import settings
from webservice.base import BaseTextResource
from B2SCrypto.utils import get_from_remote
from B2SCrypto.utils import get_key_from_local
from B2SCrypto.constant import SERVICES

class ApiKeyResource(BaseTextResource):
    def _on_get(self, req, resp, conn, **kwargs):
        return get_key_from_local(settings.PUB_KEY_PATH)


    def _on_post(self, req, resp, conn, **kwargs):
        return self._on_get(req, resp, conn, **kwargs)
