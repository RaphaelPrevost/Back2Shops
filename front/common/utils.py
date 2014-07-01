import gevent
import logging
import os
import re
import signal
import time
import uuid
import settings
from common.constants import FRT_ROUTE_ROLE
from common.redis_utils import get_redis_cli
from common.template import render_template
from B2SUtils.base_actor import as_list
from B2SProtocol.constants import INVALIDATE_CACHE_LIST
from B2SProtocol.constants import INVALIDATE_CACHE_OBJ

def gen_html_resp(template, resp, data, lang='en'):
    resp.body = render_template(template, data, lang=lang)
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
    product_info = {
        'id': id_sale,
        'name': sale.get('name') or '',
        'desc': sale.get('desc') or '',
        'img': sale.get('img') or '',
        'link': get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % id_sale,
        'price': get_product_default_display_price(sale),
        'currency': sale.get('price', {}).get('@currency') or '',
        'variant': sale.get('variant') if (isinstance(sale.get('variant'), list)
                                           or sale.get('variant') is None)
                   else [sale.get('variant')]
    }
    if not settings.PRODUCTION and not product_info['img']:
        product_info['img'] = '/img/dollar-exemple.jpg'
    return product_info

def get_brief_product_list(sales):
    return [get_brief_product(s) for s in sales.itervalues()]


def get_category_from_sales(sales):
    category = (sales.itervalues().next()).get('category')
    category_info = {
        'id': category.get('@id', ''),
        'name': category.get('name', ''),
        'img': category.get('img', ''),
        'thumb': category.get('thumb', ''),
    }
    return category_info

def get_url_format(role):
    from urls import BrandRoutes
    url_pattern = BrandRoutes().get_url_format(role)
    return re.sub(r'%\(\w+\)s', '%s', url_pattern)

def send_reload_signal():
    os.kill(os.getpid(), signal.SIGHUP)

def generate_random_key():
    return uuid.uuid4()

def watching_invalidate_cache_list():
    redis_down = False
    while True:
        try:
            cache = get_redis_cli().blpop(
                INVALIDATE_CACHE_LIST % settings.BRAND_ID, 0)
        except:
            logging.warn("Redis is down ???")
            redis_down = True
            gevent.sleep(5)
        else:
            if redis_down or cache and cache[1] == INVALIDATE_CACHE_OBJ.ROUTES:
                send_reload_signal()
            redis_down = False

