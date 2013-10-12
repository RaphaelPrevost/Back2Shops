from common.cache import sales_cache_proxy
from common.utils import gen_json_response
from webservice.base import BaseResource

class SalesResource(BaseResource):

    def _on_get(self, req, resp, conn, **kwargs):
        content = sales_cache_proxy.get(
            category=req._params.get('category'),
            shop=req._params.get('shop'),
            brand=req._params.get('brand'),
            type=req._params.get('type'))
        return gen_json_response(resp, content)

def import_sales_list():
    sales_cache_proxy.refresh()
