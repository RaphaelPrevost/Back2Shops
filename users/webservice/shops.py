from common.cache import shops_cache_proxy
from webservice.base import BaseJsonResource

class ShopsResource(BaseJsonResource):
    def _on_get(self, req, resp, conn, **kwargs):
        content = shops_cache_proxy.get(
            seller=req._params.get('seller'),
            city=req._params.get('city'))
        return content

def import_shops_list():
    shops_cache_proxy.refresh()
