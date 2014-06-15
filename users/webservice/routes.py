import xmltodict

import settings
from common.cache import routes_cache_proxy
from common.utils import get_client_ip
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context

class RoutesResource(BaseJsonResource):
    encrypt = True

    def _on_get(self, req, resp, conn, **kwargs):
        # TODO getting from BO and convert xml resp to json
        brand = req.get_param('brand', required=True)
        resp_dict = routes_cache_proxy.get(
            brand=req._params.get('brand'))

        return resp_dict

    def encrypt_resp(self, resp, content):
        client_ip = get_client_ip(self.request)
        if not client_ip:
            client_ip = settings.FRONT_ROOT_URI

        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
            content,
            '%s/webservice/1.0/pub/apikey.pem' % client_ip,
            settings.PRIVATE_KEY_PATH)
        return resp

