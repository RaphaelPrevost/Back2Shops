from B2SCrypto.constant import SERVICES
from common.cache import tax_cache_proxy
from webservice.base import BaseJsonResource

class TaxesResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.FRO

    def _on_get(self, req, resp, conn, **kwargs):
        return tax_cache_proxy.get()

