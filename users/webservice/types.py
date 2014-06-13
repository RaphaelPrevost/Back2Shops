from common.cache import types_cache_proxy
from webservice.base import BaseJsonResource

class TypesResource(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        content = types_cache_proxy.get(
            seller=req._params.get('seller'))
        return content

