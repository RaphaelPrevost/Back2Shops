from B2SCrypto.constant import SERVICES
from common.cache import routes_cache_proxy
from webservice.base import BaseJsonResource

class RoutesResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.FRO

    def _on_get(self, req, resp, conn, **kwargs):
        brand = req.get_param('brand')
        resp_dict = routes_cache_proxy.get(brand=brand)
        return resp_dict

