import settings
from webservice.base import BaseResource
from B2SCrypto.utils import get_from_remote
from B2SCrypto.utils import get_key_from_local
from B2SCrypto.constant import SERVICES

class ApiKeyResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        key = get_key_from_local(settings.PUB_KEY_PATH)
        resp.body = key
        return resp

    def _on_post(self, req, resp, conn, **kwargs):
        return self._on_get(req, resp, conn, **kwargs)

# TODO: remove, just for encrypt test.
class CryptoTestResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        adm_test_uri = settings.SALES_SERVER_API_URL % {'api': 'pub/crypto/test?from=USR'}
        remote_server_name = SERVICES.ADM
        try:
            content = get_from_remote(adm_test_uri,
                                      settings.SERVER_APIKEY_URI_MAP[remote_server_name],
                                      settings.PRIVATE_KEY_PATH)
        except Exception, e:
            import logging
            logging.error('Met error %s', e, exc_info=True)
            raise
        resp.body = content
        return resp


