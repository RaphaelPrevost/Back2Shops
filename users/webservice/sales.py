from common.cache import sale_cache_proxy
from webservice.base import BaseJsonResource

class SalesResource(BaseJsonResource):

    def _on_get(self, req, resp, conn, **kwargs):
        content = sale_cache_proxy.get(
            category=req._params.get('category'),
            shop=req._params.get('shop'),
            brand=req._params.get('brand'),
            type=req._params.get('type'))
        return content

def import_sales_list():
    sale_cache_proxy.refresh()
