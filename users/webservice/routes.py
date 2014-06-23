import settings
from common.cache import routes_cache_proxy
from common.utils import get_client_ip
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context

class RoutesResource(BaseJsonResource):
    encrypt = True
    service = SERVICES.FRO

    def _on_get(self, req, resp, conn, **kwargs):
        brand = req.get_param('brand')
        resp_dict = routes_cache_proxy.get(brand=brand)
        return resp_dict

