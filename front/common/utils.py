# -*- coding: utf-8 -*-
import settings
import datetime
import gevent
import logging
import os
import signal
import ujson
import uuid
import xmltodict

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SFrontUtils.utils import normalize_name
from B2SProtocol.constants import INVALIDATE_CACHE_LIST
from B2SProtocol.constants import INVALIDATE_CACHE_OBJ
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SProtocol.constants import USER_BASKET
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME
from B2SUtils.base_actor import as_list
from B2SUtils.common import get_cookie_value
from B2SUtils.common import set_cookie
from common.constants import ADDR_TYPE
from common.constants import FRT_ROUTE_ROLE
from common.constants import CURR_USER_BASKET_COOKIE_NAME
from common.redis_utils import get_redis_cli
from common.template import render_template


def gen_html_resp(template, resp, data, lang='en'):
    resp.body = render_template(template, data,
                                lang=lang,
                                layout=settings.DEFAULT_TEMPLATE,
                                )
    resp.content_type = "text/html"
    return resp

def unicode2utf8(data):
    """Convert unicode string's into utf-8 encoding
    This utility function will accept dict and list data structures.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key = unicode2utf8(key)
            value = unicode2utf8(value)
            result[key] = value
    elif isinstance(data, list):
        result = []
        for value in data:
            value = unicode2utf8(value)
            result.append(value)
    elif isinstance(data, unicode):
        result = data.encode('utf-8')
    else:
        result = data
    return result

def valid_int_param(req, param_name):
    try:
        assert int(req.get_param(param_name)) > 0
        return True
    except:
        return False

def cur_symbol(cur_code):
    return {
        'EUR': '€',
    }.get(cur_code, cur_code)

def format_amount(amount):
    try:
        return '%.2f' % float(amount)
    except:
        return amount

def format_date(date_str, from_format='%Y-%m-%d', to_format='%d %b %Y'):
    try:
        return datetime.datetime.strptime(date_str, from_format).strftime(to_format)
    except:
        return date_str

def get_product_default_display_price(sale):
    price = sale.get('price', {}).get('#text') or ''
    if not price:
        for type_attr in as_list(sale.get('type', {}).get('attribute')):
            if 'price' in type_attr:
                price = type_attr['price'].get('#text')
                break
    return price

def get_brief_product(sale):
    id_sale = sale['@id']
    _type = sale.get('type', {})
    product_info = {
        'id': id_sale,
        'name': sale.get('name') or '',
        'desc': sale.get('desc') or '',
        'img': sale.get('img') or '',
        'link': get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % {
            'id_type': _type.get('@id', 0),
            'type_name': get_normalized_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                             'type_name',
                                             _type.get('name', '')),
            'id_sale': id_sale,
            'sale_name': get_normalized_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                             'sale_name',
                                             sale.get('name', '')),
        },
        'price': get_product_default_display_price(sale),
        'currency': sale.get('price', {}).get('@currency') or '',
        'variant': as_list(sale.get('variant')),
    }
    if not settings.PRODUCTION and not product_info['img']:
        product_info['img'] = '/img/dollar-example.jpg'
    return product_info

def get_brief_product_list(sales):
    return [get_brief_product(s) for s in sales.itervalues()]

def get_category_from_sales(sales):
    if len(sales) > 0:
        category = (sales.itervalues().next()).get('category')
    else:
        category = {}
    category_info = {
        'id': category.get('@id', ''),
        'name': category.get('name', ''),
        'img': category.get('img', ''),
        'thumb': category.get('thumb', ''),
    }
    return category_info

def get_type_from_sale(sale):
    _type = sale.get('type', {})
    type_info = {
        'id': _type.get('@id', ''),
        'name': _type.get('name', '')
    }
    return type_info

def get_user_contact_info(user_info_resp):
    try:
        shipping_address = None
        billing_address = None
        for addr in user_info_resp['address']['values']:
            if addr['addr_type'] == ADDR_TYPE.Billing:
                billing_address = addr
            else:
                shipping_address = addr
        if not billing_address:
            billing_address = shipping_address
        id_phone = user_info_resp['phone']['values'][0]['id']
    except:
        shipping_address = billing_address = None
        id_phone = 0
    data = {'billing_address': billing_address,
            'shipping_address': shipping_address,
            'id_phone': id_phone}
    return data

def get_basket(req, resp, cookie_name=None):
    basket_key = None
    basket_data = None
    if cookie_name:
        iternames = [cookie_name]
    else:
        iternames = [CURR_USER_BASKET_COOKIE_NAME, USER_BASKET_COOKIE_NAME]
    for c_name in iternames:
        basket_key = get_cookie_value(req, c_name)
        try:
            if basket_key:
                basket_data = get_redis_cli().get(basket_key)
                if basket_data: break
        except:
            pass

    if not basket_key:
        basket_key = USER_BASKET % generate_random_key()
        set_cookie(resp, USER_BASKET_COOKIE_NAME, basket_key)
    basket_data = ujson.loads(basket_data) if basket_data else {}
    return basket_key, basket_data

def clear_basket(req, resp, basket_key, basket_data):
    # called after the order placed successfully

    redis_cli = get_redis_cli()
    if basket_key == get_cookie_value(req, USER_BASKET_COOKIE_NAME):
        redis_cli.set(basket_key, ujson.dumps({}))

    elif basket_key == get_cookie_value(req, CURR_USER_BASKET_COOKIE_NAME):
        redis_cli.delete(basket_key)

        prev_basket_key, prev_basket_data = get_basket(req, resp, USER_BASKET_COOKIE_NAME)
        [prev_basket_data.pop(item) for item in basket_data
                                    if item in prev_basket_data]
        redis_cli.set(prev_basket_key, ujson.dumps(prev_basket_data))

    set_cookie(resp, CURR_USER_BASKET_COOKIE_NAME, "")

def get_valid_attr(attrlist, attr_id):
    if not attr_id or not attrlist:
        return {}

    attrlist = as_list(attrlist)
    for attr in attrlist:
        if attr['@id'] == str(attr_id):
            return attr
    return {}

def get_basket_table_info(req, resp, basket_data):
    # basket_data dict:
    # - key is json string
    #   {"id_sale": **, "id_shop": **, "id_attr": **, "id_variant": **, "id_price_type": **}
    # - value is quantity

    from common.data_access import data_access
    all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
    basket = []
    for item, quantity in basket_data.iteritems():
        item_info = ujson.loads(item)
        id_sale = str(item_info['id_sale'])
        if id_sale not in all_sales:
            continue

        sale_info = all_sales[id_sale]
        basket.append({
            'item': item,
            'quantity': quantity,
            'variant': get_valid_attr(
                        sale_info.get('variant'),
                        item_info.get('id_variant')),
            'type': get_valid_attr(
                        sale_info.get('type', {}).get('attribute'),
                        item_info.get('id_attr')),
            'product': get_brief_product(sale_info)
        })
    return basket


def get_shipping_info(req, resp, order_id):
    from common.data_access import data_access
    xml_resp = data_access(REMOTE_API_NAME.GET_SHIPPING_LIST,
                           req, resp, id_order=order_id)
    shipments = xmltodict.parse(xml_resp)['shipments']
    shipment_info = {}
    need_select_carrier = False
    for shipment in as_list(shipments['shipment']):
        method = int(shipment['@method'])
        if method == SCM.CARRIER_SHIPPING_RATE:
            if not shipment['delivery'].get('@postage'):
                xml_resp = data_access(REMOTE_API_NAME.GET_SHIPPING_FEE,
                                       req, resp, shipment=shipment['@id'])

                carriers = xmltodict.parse(xml_resp)['carriers']
                shipment['delivery'].update({'carrier': carriers['carrier']})
                need_select_carrier = True
        else:
            pass

        shipment['delivery'].update({'carrier':
                                     as_list(shipment['delivery'].get('carrier'))})
        for car in shipment['delivery']['carrier']:
            car['service'] = as_list(car['service'])
        shipment['item'] = as_list(shipment['item'])
        shipment['@method'] = SCM.toReverseDict().get(int(shipment['@method']))
        shipment_info[shipment['@id']] = shipment

    data = {
        'order_id': order_id,
        'order_created': format_date(shipments['@order_create_date']),
        'shipments_detail': shipment_info,
        'need_select_carrier': need_select_carrier,
    }
    return data

def get_order_table_info(order_id, order_resp, all_sales):
    user_name = '%s %s %s' % (
            order_resp['user_info']['title'],
            order_resp['user_info']['first_name'],
            order_resp['user_info']['last_name'],
            )

    order_items = []
    shipments = {}
    for item in order_resp.get('order_items', []):
        for item_id, item_info in item.iteritems():
            id_sale = str(item_info['sale_id'])
            if id_sale not in all_sales:
                continue

            sale_info = all_sales[id_sale]
            order_items.append({
                'id_sale': id_sale,
                'quantity': item_info['quantity'],
                'variant': get_valid_attr(
                            sale_info.get('variant'),
                            item_info.get('id_variant')),
                'type': get_valid_attr(
                            sale_info.get('type', {}).get('attribute'),
                            item_info.get('id_price_type')),
                'product': get_brief_product(sale_info),
            })

            for _shipment_info in item_info['shipment_info']:
                shipment_id = _shipment_info.get('shipment_id')
                if not shipment_id:
                    # sth. wrong when create order
                    continue
                shipping_list = _shipment_info.copy()
                shipping_list['item'] = order_items[-1]
                shipping_list['status_name'] = SHIPMENT_STATUS.toReverseDict().get(
                                               int(shipping_list['status']))
                if shipment_id not in shipments:
                    shipments[shipment_id] = []
                shipments[shipment_id].append(shipping_list)
    data = {
        'order_id': order_id,
        'status_name': ORDER_STATUS.toReverseDict().get(
                       int(order_resp['order_status'])),
        'user_name': user_name,
        'shipments': shipments,
    }
    return data


def get_url_format(role):
    from urls import BrandRoutes
    return BrandRoutes().get_url_format(role)

def get_normalized_name(role, _type, name):
    from urls import BrandRoutes
    meta = BrandRoutes().get_meta_by_role(role)
    return (meta.get(_type, None) or
            _type in ROUTE_NAME_MAPPING and ROUTE_NAME_MAPPING[_type](name) or
            name)

def is_routed_template(role):
    from urls import BrandRoutes
    return BrandRoutes().is_routed(role)

def send_reload_signal():
    logging.info("Send reload signal...")
    os.kill(os.getpid(), signal.SIGHUP)

def generate_random_key():
    return uuid.uuid4()

def watching_invalidate_cache_list():
    redis_down = False
    redis_cli = get_redis_cli()
    key = INVALIDATE_CACHE_LIST % settings.BRAND_ID
    while True:
        try:
            cache = None
            if redis_cli.exists(key):
                cache = redis_cli.blpop(key, 0)
            else:
                gevent.sleep(5)
        except:
            logging.warn("Redis is down ???")
            redis_down = True
            gevent.sleep(5)
        else:
            if redis_down or cache and cache[1] == INVALIDATE_CACHE_OBJ.ROUTES:
                send_reload_signal()
            redis_down = False


ROUTE_NAME_MAPPING = {
    'type_name': normalize_name,
    'sale_name': normalize_name,
}
