from common.cache import shops_cache_proxy
from common.utils import gen_json_response
from webservice.base import BaseResource

class ShopsResource(BaseResource):
    def _on_get(self, req, resp, conn, **kwargs):
        content = shops_cache_proxy.get(
            seller=req._params.get('seller'),
            city=req._params.get('city'))
        return gen_json_response(resp, content)

def import_shops_list():
    shops_cache_proxy.refresh()
