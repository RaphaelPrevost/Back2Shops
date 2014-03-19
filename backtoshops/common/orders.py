import settings
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from common.error import UsersServerError

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


def get_order_list(brand_id, shops_id=None):
    try:
        order_url = '%s?brand_id=%s' % (settings.ORDER_LIST_URL, brand_id)
        if shops_id:
            order_url += "&shops_id=%s" % ujson.dumps(shops_id)
        data = get_from_remote(
            order_url,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            headers={'Content-Type': 'application/json'}
        )
        return ujson.loads(data)
    except Exception, e:
        logging.error('Failed to get order list from usr servers',
                      exc_info=True)
        raise UsersServerError


def get_order_detail(order_id, brand_id, shops_id):
    try:
        url = '%s?id=%s&brand_id=%s' % (settings.ORDER_DETAIL_URL,
                                        order_id, brand_id)
        if shops_id:
            url += "&shops_id=%s" % ujson.dumps(shops_id)
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
        raise UsersServerError

def get_order_packing_list(order_id):
    try:
        url = '%s?id_order=%s' %  (settings.ORDER_SHIPPING_LIST,
                                   order_id)
        data = get_from_remote(
            url,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH
        )
        return data
    except Exception, e:
        logging.error('Failed to get order(id=%s) shipping list from '
                      'usr servers: %s',
                      order_id, e, exc_info=True)
        raise UsersServerError

def send_new_shipment(id_order, id_shipment, handling_fee, shipping_fee, content):
    if isinstance(content, list):
        content = ujson.dumps(content)

    try:
        data = {'action': 'create',
                'order': id_order,
                'handling_fee': handling_fee,
                'shipping_fee': shipping_fee,
                'id_orig_shipment': id_shipment,
                'content': content}
        data = ujson.dumps(data)
        data = gen_encrypt_json_context(
            data,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        rst = get_from_remote(
            settings.ORDER_SHIPMENT,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return rst
    except Exception, e:
        logging.error('Failed to create shipment %s,'
                      'error: %s',
            {'id_order': id_order,
             'id_shipment': id_shipment,
             'content': content}, e, exc_info=True)
        raise UsersServerError

def send_update_shipment(id_shipment, shipping_fee=None, handling_fee=None,
                         status=None, tracking_num=None, content=None,
                         shipping_date=None):
    if isinstance(content, list):
        content = ujson.dumps(content)

    try:
        data = {}
        if shipping_fee:
            data['shipping_fee'] = shipping_fee
        if handling_fee:
            data['handling_fee'] = handling_fee
        if status:
            data['status'] = status
        if tracking_num:
            data['tracking'] = tracking_num
        if content:
            data['content'] = content
        if shipping_date:
            data['shipping_date'] = shipping_date

        if not data:
            return

        data['shipment'] = id_shipment
        data['action'] = 'modify'
        data = ujson.dumps(data)
        data = gen_encrypt_json_context(
            data,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        rst = get_from_remote(
            settings.ORDER_SHIPMENT,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return rst

    except Exception, e:
        logging.error('Failed to update shipment %s,'
                      'error: %s',
                      {'id_shipment': id_shipment,
                       'shipping_fee': shipping_fee,
                       'handling_fee': handling_fee,
                       'status': status,
                       'tracking_num': tracking_num,
                       'content': content}, e, exc_info=True)
        raise UsersServerError


def send_delete_shipment(id_shipment):
    try:
        data = {'action': 'delete',
                'shipment': id_shipment}
        data = ujson.dumps(data)
        data = gen_encrypt_json_context(
            data,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH)
        rst = get_from_remote(
            settings.ORDER_SHIPMENT,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return rst
    except Exception, e:
        logging.error('Failed to delete shipment %s,'
                      'error: %s',
                      {'id_shipment': id_shipment}, e, exc_info=True)
        raise UsersServerError
