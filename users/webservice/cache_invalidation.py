import settings
import gevent
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from common import cache
from common.constants import RESP_RESULT
from webservice.base import BaseJsonResource

class InvalidationResource(BaseJsonResource):

    def on_post(self, req, resp, **kwargs):
        try:
            data = decrypt_json_resp(req.stream,
                                settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                settings.PRIVATE_KEY_PATH)
            logging.info("Received cache invalidation %s" % data)
            method, obj_name, obj_id = data.split('/')
        except Exception, e:
            logging.error("Got exceptions when decrypting invalidation data",
                          exc_info=True)
            self.gen_resp(resp, {'res': RESP_RESULT.F})
        else:
            self.gen_resp(resp, {'res': RESP_RESULT.S})
            gevent.spawn(refresh_cache, method, obj_name, obj_id)


    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps(data_dict),
                            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                            settings.PRIVATE_KEY_PATH)
        return resp


def refresh_cache(method, obj_name, obj_id):
    proxy = getattr(cache, '%ss_cache_proxy' % obj_name, None)
    if proxy is None:
        logging.error("No cache_proxy object for %s" % obj_name)
        return

    if method == 'DELETE':
        proxy.del_obj(obj_id)
    else:
        proxy.refresh(obj_id)

    proxy.cached_query_invalidate(obj_id, method)

