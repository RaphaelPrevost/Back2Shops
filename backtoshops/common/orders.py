import settings
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote

def send_shipping_fee(id_shipment, id_postage, shipping_fee):
    try:
        data = {'id_shipment': id_shipment,
                'id_postage': id_postage,
                'shipping_fee': shipping_fee}
        data = ujson.dumps(data)
        logging.info("Send shipping fee %s" % data)

        data = gen_encrypt_json_context(data,
                    settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                    settings.PRIVATE_KEY_PATH)

        rst = get_from_remote(settings.SHIPPING_FEE_URL,
                        settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                        settings.PRIVATE_KEY_PATH,
                        data=data,
                        headers={'Content-Type': 'application/json'})
    except Exception, e:
        logging.error("Failed to send shipping fee %s" % data,
                      exc_info=True)

