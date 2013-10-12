import settings
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from common.constants import RESP_RESULT
from webservice.base import BaseResource

class InvalidationResource(BaseResource):

    def on_post(self, req, resp, **kwargs):
        try:
            data = decrypt_json_resp(req.stream,
                                settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                settings.PRIVATE_KEY_PATH)
            logging.info("Received cache invalidation %s" % data)
            method, item_name, item_id = data.split('/')
        except Exception, e:
            logging.error("Got exceptions when decrypting invalidation data",
                          exc_info=True)
            self.gen_resp(resp, {'res': RESP_RESULT.F})
        else:
            #TODO update items in redis

            self.gen_resp(resp, {'res': RESP_RESULT.S})

    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps({'res': RESP_RESULT.S}),
                            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                            settings.PRIVATE_KEY_PATH)
        return resp

