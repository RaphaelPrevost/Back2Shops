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


def get_order_list(mother_brand_id=None):
    try:
        url = settings.ORDER_LIST_URL
        if mother_brand_id:
            url += '?mother_brand_id=%s' % mother_brand_id
        data = get_from_remote(
            url,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            headers={'Content-Type': 'application/json'}
        )
        return ujson.loads(data)
    except Exception, e:
        logging.error('Failed to get order list from usr servers',
                      exc_info=True)


def get_order_detail(order_id, mother_brand_id=None):
    try:
        url = '%s?id=%s' % (settings.ORDER_DETAIL_URL, order_id)
        if mother_brand_id:
            url += '&mother_brand_id=%s' % mother_brand_id
        data = get_from_remote(
            url,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            headers={'Content-Type': 'application/json'}
        )
        return ujson.loads(data)
    except Exception, e:
        logging.error('Failed to get order(id=%s) detail from usr servers',
                      order_id, exc_info=True)
