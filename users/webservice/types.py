from common.cache import type_cache_proxy
from webservice.base import BaseJsonResource

class TypesResource(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        content = type_cache_proxy.get(
            seller=req._params.get('seller'))
        return content

