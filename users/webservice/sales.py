import urllib

from common.cache import cache_proxy
from webservice.base import BaseResource

class SalesResource(BaseResource):

    def on_get(self, req, resp, **kwargs):
        allowed_params = ('type', 'category', 'shop', 'brand')
        query_str = urllib.urlencode([(p, req._params[p]) for p in req._params
                                      if p in allowed_params])
        content = cache_proxy.get(get_redis_key(query_str))

        resp.content_type = "text/xml"
        resp.body = content
        return resp

def get_redis_key(query_str=''):
    return "pub/sales/list?%s" % query_str

def import_sales_list():
    cache_proxy.refresh(get_redis_key())
