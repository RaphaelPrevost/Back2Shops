from common.cache import types_cache_proxy
from webservice.base import BaseJsonResource

class TypesResource(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        content = types_cache_proxy.get(
            seller=req._params.get('brand'))
        return content

def import_types_list():
    types_cache_proxy.refresh()
