import settings
import logging

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote


def post_save_handler(item_name, sender, **kwargs):
    method = kwargs.get('created', False) and "POST" or "PUT"
    instance = kwargs.get('instance')
    send_cache_invalidation(method, item_name, instance.id)

def post_delete_handler(item_name, sender, **kwargs):
    method = "DELETE"
    instance = kwargs.get('instance')
    send_cache_invalidation(method, item_name, instance.id)

def send_cache_invalidation(method, item_name, item_id):
    try:
        invalidation = '%s/%s/%s' % (method, item_name, item_id)
        logging.info("Sending cache invalidation %s" % invalidation)

        data = gen_encrypt_json_context(invalidation,
                    settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                    settings.PRIVATE_KEY_PATH)

        get_from_remote(settings.CACHE_INVALIDATION_URL,
                        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                        settings.PRIVATE_KEY_PATH,
                        data=data,
                        headers={'Content-Type': 'application/json'})
    except Exception, e:
        logging.error("Failed to send cache invalidation %s" % invalidation,
                      exc_info=True)

