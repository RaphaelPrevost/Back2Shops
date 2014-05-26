import xmltodict

import settings
from common.utils import get_client_ip
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context

class RoutesResource(BaseJsonResource):
    encrypt = True

    def _on_get(self, req, resp, conn, **kwargs):
        # TODO getting from BO and convert xml resp to json
        brand = req.get_param('brand', required=True)
        resp_dict = xmltodict.parse("""
<routes version="1.0">
<route id="456" modified="date">
    <url>/coins.html</url>
    <template>PRDT_LIST</template>
    <meta name="title">page title</meta>
    <content>descriptions</content>
</route>
<route id="321" modified="date">
    <url>/old_coins/(\p{L}+?).html</url>
    <param number="1" required="true">sale_id</param>
    <template>PRDT_INFO</template>
    <meta name="title">page title</meta>
    <content>description</content>
    <redirect to="123">
        <map param="1" to="1" />
    </redirect>
</route>
<route id="123" modified="date">
    <url>/coins/(\p{L}+?).html</url>
    <param number="1" required="true">id_sale</param>
    <template>PRDT_INFO</template>
    <meta name="title">page title</meta>
    <content>description</content>
</route>
</routes>""")
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

