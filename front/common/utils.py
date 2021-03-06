# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


import base64
import settings
import HTMLParser
import datetime
import gevent
import logging
import os
import random
import signal
import time
import ujson
import uuid
import xmltodict
import M2Crypto

from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SFrontUtils.geolocation import get_location_by_ip
from B2SFrontUtils.utils import get_thumbnail_url
from B2SFrontUtils.utils import normalize_name
from B2SProtocol.constants import EURO_UNION_COUNTRIES
from B2SProtocol.constants import EXPIRY_FORMAT
from B2SProtocol.constants import BRANDSETTING
from B2SProtocol.constants import INVALIDATE_CACHE_LIST
from B2SProtocol.constants import INVALIDATE_CACHE_OBJ
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM
from B2SProtocol.constants import USER_BASKET
from B2SProtocol.constants import USER_BASKET_COOKIE_NAME
from B2SUtils.base_actor import as_list
from B2SUtils.common import get_cookie_value
from B2SUtils.common import localize_datetime
from B2SUtils.common import parse_ts
from B2SUtils.common import set_cookie
from B2SUtils.common import to_round
from common.constants import ADDR_TYPE
from common.constants import FRT_ROUTE_ROLE
from common.constants import CURR_USER_BASKET_COOKIE_NAME
from common.m17n import gettext as _
from common.redis_utils import get_redis_cli
from common.template import render_template


def gen_html_resp(template, resp, data,
                  lang=settings.DEFAULT_LOCALE,
                  layout=settings.DEFAULT_TEMPLATE):
    resp.body = gen_html_body(template, data,
                              lang=lang,
                              layout=layout)
    resp.content_type = "text/html"
    return resp

def gen_html_body(template, data,
                  lang=settings.DEFAULT_LOCALE,
                  layout=settings.DEFAULT_TEMPLATE):
    return render_template(template, data,
                           lang=lang,
                           layout=layout,
                          )

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

def valid_int(value, non_zero=True):
    try:
        if non_zero:
            assert int(value) > 0
        else:
            assert int(value) >= 0
        return True
    except:
        return False

def cur_symbol(cur_code):
    return {
        'EUR': '€',
        'USD': '$',
    }.get(cur_code, cur_code)

def zero(amount):
    try:
        return not amount or float(amount) == 0
    except:
        return False

def format_amount(amount, decimal_digits=2):
    try:
        result = ('%%.%sf' % decimal_digits) % to_round(amount, decimal_digits)
        if decimal_digits > 2:
            count = decimal_digits - 2
            while count > 0:
                if result[-1] == '0':
                    result = result[:-1]
                    count -= 1
                    continue
                else:
                    break
        return result
    except:
        return amount

def format_date(date_str, days=0,
                from_format='%Y-%m-%d', to_format='%d/%m/%Y'):
    try:
        return (datetime.datetime.strptime(date_str, from_format)
              + datetime.timedelta(days=days)).strftime(to_format)
    except:
        return date_str

def format_epoch_time(seconds, format='%d/%m/%Y'):
    return time.strftime(format, time.gmtime(seconds))

def allowed_countries():
    if settings.BRAND_NAME == 'BREUER':
        return EURO_UNION_COUNTRIES
    return []

def user_is_business_account(req, resp, users_id):
    is_b_account = False
    if users_id:
        from common.data_access import data_access
        user_info = data_access(REMOTE_API_NAME.GET_USERINFO, req, resp)
        general_user_values = user_info['general']['values'][0]
        is_b_account = general_user_values.get('is_business_account', False)
    else:
        front_personal_account_allowed = get_adm_settings(
            'front_personal_account_allowed', req, resp) == 'True'
        front_business_account_allowed = get_adm_settings(
            'front_business_account_allowed', req, resp) == 'True'
        if not front_personal_account_allowed and \
                front_business_account_allowed:
            is_b_account = True
    return is_b_account

def calc_before_tax_price(req, resp):
    return get_adm_settings('use_after_tax_price', req, resp) == 'True'

def use_unique_items(req, resp):
    return get_adm_settings('unique_items', req, resp) == 'True'

def get_adm_settings(name, req, resp):
    from common.data_access import data_access
    settings_list = data_access(REMOTE_API_NAME.ADM_SETTINGS, req, resp)
    return settings_list.get(name)


def get_price_label(need_calc_before_tax):
    return _("Before tax") if need_calc_before_tax else _("After tax")

def get_product_default_display_price(sale, type_attr=None):
    ori_price = sale.get('price', {}).get('#text') or ''
    discount_price = sale.get('discount_price')
    valid_from = sale.get('discount', {}).get('@from') or ''
    valid_to = sale.get('discount', {}).get('@to') or ''
    if type_attr:
        if 'price' in type_attr:
            ori_price = type_attr['price'].get('#text')
            discount_price = type_attr.get('discount_price')
    else:
        for type_attr in as_list(sale.get('type', {}).get('attribute')):
            if 'price' in type_attr:
                ori_price = type_attr['price'].get('#text')
                discount_price = type_attr.get('discount_price')
                break
    if not discount_price:
        discount_price = ori_price

    now = datetime.datetime.utcnow()
    if valid_from and parse_ts(valid_from) > now \
            or valid_to and parse_ts(valid_to) < now:
        discount_price = ori_price
    return float(ori_price), float(discount_price)

def cal_price_with_premium(variant, price):
    price = float(price)
    if variant:
        p_type = variant.get("premium", {}).get("@type", 0)
        p_amount = float(variant.get("premium", {}).get("#text", 0))
        if p_type:
            if p_type == 'fixed':
                price += p_amount
            elif p_type == 'ratio':
                price *= (1 + p_amount/100)
    return price

def _get_brand_addr(sale_info):
    country_code = province_code = None
    addr = sale_info.get('brand', {}).get('address', {}).get('country')
    if addr and addr.get("#text"):
        country_code = addr["#text"]
        province_code = addr.get("@province")
    return country_code, province_code

def _get_shop_addr(sale_info, id_shop=None):
    country_code = province_code = None
    for shop in as_list(sale_info.get('shop')):
        if id_shop and shop['@id'] != str(id_shop):
            continue
        addr = shop.get('address', {}).get('country')
        if addr and addr.get("#text"):
            country_code = addr["#text"]
            province_code = addr.get("@province")
        break
    return country_code, province_code

def get_brief_product(sale, req, resp, calc_price=True,
                      is_business_account=False):
    id_sale = sale['@id']
    _type = sale.get('type', {})
    short_desc = sale.get('short_desc') or ''
    if short_desc == 'None':
        short_desc = ''
    product_info = {
        'id': id_sale,
        'name': sale.get('name') or '',
        'desc': sale.get('desc') or '',
        'short_desc': short_desc,
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
        'currency': sale.get('price', {}).get('@currency') or '',
        'variant': as_list(sale.get('variant')),
    }

    if calc_price:
        price = get_product_default_display_price(sale)[1]
        for v in product_info['variant']:
            price = cal_price_with_premium(v, price)
            break

        country_code, province_code = _get_shop_addr(sale)
        if not country_code:
            country_code, province_code = _get_brand_addr(sale)
        _cate_id = sale.get('category', {}).get('@id', 0)
        #TODO: call user_country_province() to get user location ??
        user_country_code, user_province_code = None, None
        tax_info = get_category_tax_info(req, resp,
                country_code, province_code,
                user_country_code, user_province_code,
                _cate_id, is_business_account)
        product_info['price'] = price
        if calc_before_tax_price(req, resp):
            product_info['price_with_tax_calc'] = price * (1 + tax_info['rate'] / 100.0)
        else:
            product_info['price_with_tax_calc'] = price / (1 + tax_info['rate'] / 100.0)
        product_info['show_final_price'] = tax_info['show_final_price']

    if not settings.PRODUCTION and not product_info['img']:
        product_info['img'] = '/img/dollar-example.jpg'
    return product_info

def parse_date(date_str):
    return datetime.datetime.strptime(date_str[:10], '%Y-%m-%d').date()

def get_brief_product_list(sales, req, resp, users_id):
    is_business_account = user_is_business_account(req, resp, users_id)
    now = datetime.datetime.utcnow().date()
    return [get_brief_product(s, req, resp,
                is_business_account=is_business_account)
            for s in sales.itervalues()
            if int(s.get('available', {}).get('@total', 0)) > 0
            and (not s.get('available', {}).get('@from')
                 or parse_date(s.get('available', {}).get('@from')) <= now)
            and (not s.get('available', {}).get('@to')
                 or parse_date(s.get('available', {}).get('@to')) >= now)
            ]

def get_random_products(sales, req, resp, users_id,
                        count=settings.NUM_OF_RANDOM_SALES):
    random_sales = {}
    if len(sales) < count:
        count = len(sales)
    map(lambda k: random_sales.update({k: sales[k]}),
        random.sample(sales, count))
    return get_brief_product_list(random_sales, req, resp, users_id)

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
        'name': '' if _type.get('@default') == 'True' else _type.get('name', '')
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

def user_country_province(req, resp, users_id):
    # only calculate worldwide taxes which is independent
    # of user location
    return None, None
#    from common.data_access import data_access
#    if users_id:
#        user_info_resp = data_access(REMOTE_API_NAME.GET_USERINFO, req, resp)
#        addr = get_user_contact_info(user_info_resp).get('shipping_address', {})
#        country_code = addr.get('country_code')
#        province_code = addr.get('province_code')
#    else:
#        geolocation = get_location_by_ip(get_client_ip(req))
#        country_code = geolocation['country']['iso_code']
#        province_code = ''
#    return country_code, province_code


def get_category_tax_info(req, resp,
                     from_country_code, from_province_code,
                     to_country_code, to_province_code,
                     category_id, is_business_account):
    from common.data_access import data_access
    taxes = data_access(REMOTE_API_NAME.GET_TAXES, req, resp,
                        fromCountry=from_country_code,
                        fromProvince=from_province_code,
                        toCountry=to_country_code,
                        toProvince=to_province_code,
                        category=category_id)
    rate = 0
    show_final_price = False
    for t in taxes.itervalues():
        if (is_business_account and
                t.get('applies_to_personal_accounts') == 'True' or
           not is_business_account and
                t.get('applies_to_business_accounts') == 'True'):
            continue

        rate = float(t['rate'])
        show_final_price = t.get('display_on_front') == 'True'
        break

    return {'rate': rate, 'show_final_price': show_final_price}

def get_basket_table_info(req, resp, basket_data, users_id):
    # basket_data dict:
    # - key is json string
    #   {"id_sale": **, "id_shop": **, "id_attr": **, "id_variant": **, "id_price_type": **}
    # - value is quantity

    from common.data_access import data_access
    all_sales = data_access(REMOTE_API_NAME.GET_SALES, req, resp)
    user_country_code, user_province_code = \
            user_country_province(req, resp, users_id)
    is_business_account = user_is_business_account(req, resp, users_id)
    basket = []
    for item, quantity in basket_data.iteritems():
        try:
            item_info = ujson.loads(item)
        except:
            continue
        id_sale = str(item_info['id_sale'])
        id_shop = str(item_info['id_shop'])
        if id_sale not in all_sales:
            continue

        sale_info = all_sales[id_sale]
        _type = sale_info.get('type', {})

        variant = get_valid_attr(
                        sale_info.get('variant'),
                        item_info.get('id_variant'))
        type =  get_valid_attr(
                        sale_info.get('type', {}).get('attribute'),
                        item_info.get('id_attr'))

        id_variant = variant.get('@id')
        id_type = type.get('@id')

        external_id = ''
        external_list = sale_info.get('external') or []
        if external_list and not isinstance(external_list, list):
            external_list = [external_list]
        for external in external_list:
            if ((id_variant and id_variant == external.get('@variant') or not id_variant) and
                (id_type and id_type == external.get('@attribute') or not id_type)):
                external_id = external.get('#text')
                break

        one = {
            'id_sale': id_sale,
            'item': item,
            'quantity': quantity,
            'variant': variant,
            'type': type,
            'product': get_brief_product(sale_info, req, resp,
                calc_price=False,
                is_business_account=is_business_account),
            'link': get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % {
                'id_type': _type.get('@id', 0),
                'type_name': get_normalized_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                                 'type_name',
                                                 _type.get('name', '')),
                'id_sale': id_sale,
                'sale_name': get_normalized_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                                 'sale_name',
                                                 sale_info.get('name', '')),
            },
            'external_id': external_id
        }
        price = get_product_default_display_price(sale_info, one['type'])[1]
        if one['variant']:
            price = cal_price_with_premium(one['variant'], price)
        one['price'] = price

        if int(id_shop):
            country_code, province_code = _get_shop_addr(sale_info, id_shop)
        else:
            country_code, province_code = _get_brand_addr(sale_info)
        _cate_id = sale_info.get('category', {}).get('@id', 0)
        tax_info = get_category_tax_info(req, resp,
                country_code, province_code,
                user_country_code, user_province_code,
                _cate_id, is_business_account)
        if calc_before_tax_price(req, resp):
            one['price_with_tax_calc'] = price / (1 + tax_info['rate'] / 100.0)
        else:
            one['price_with_tax_calc'] = price * (1 + tax_info['rate'] / 100.0)
        one['tax'] = one['price_with_tax_calc'] - price
        one['show_final_price'] = tax_info['show_final_price']
        one['out_of_stock'] = _out_of_stock(sale_info,
                                id_variant, id_type, id_shop, quantity)

        basket.append(one)
    return basket

def _out_of_stock(sale_info, id_variant, id_type, id_shop, quantity):
    if not id_variant: id_variant = ''
    if not id_type: id_type = ''
    if not id_shop or id_shop == '0': id_shop = ''
    for stock in as_list(sale_info['available'].get('stocks')):
        if stock['@attribute'] == str(id_type) and stock['@variant'] == str(id_variant):
            for s in as_list(stock.get('stock')):
                if s['@shop'] == str(id_shop):
                    if int(s['#text']) < quantity:
                        return True
                    break
            break
    return False

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

def get_order_table_info(order_id, order_resp, all_sales=None):
    user_profile = order_resp['user_info']
    user_name = '%s %s %s' % (
                    user_profile.get('title') or '',
                    user_profile.get('first_name') or '',
                    user_profile.get('last_name') or '',
                )
    dest_user_name = order_resp['shipping_dest']['full_name'] or user_name
    dest_addr = ' '.join([
            order_resp['shipping_dest']['address'],
            order_resp['shipping_dest']['postalcode'],
            order_resp['shipping_dest']['city'],
            order_resp['shipping_dest']['province'],
            order_resp['shipping_dest']['country'],
    ])
    order_items = []
    shipments = {}
    order_status = int(order_resp['order_status'])
    order_created = format_epoch_time(order_resp['confirmation_time'])
    for item_id, item_info in order_resp.get('order_items', []):
        id_sale = str(item_info['sale_id'])

        if item_info['id_variant'] == 0:
            product_name = item_info['name']
            variant_name = ''
        else:
            product_name, variant_name = item_info['name'].rsplit('-', 1)
        one = {
            'id_sale': id_sale,
            'quantity': item_info['quantity'],
            'product_name': product_name,
            'variant_name': variant_name,
            'type_name': item_info.get('type_name') or '',
            'price': item_info['price'],
            'picture': item_info['picture'],
            'external_id': item_info['external_id'],
        }

        sale_info = None
        if all_sales and id_sale in all_sales:
            sale_info = all_sales[id_sale]
            _type = sale_info.get('type', {})
            one['link'] = get_url_format(FRT_ROUTE_ROLE.PRDT_INFO) % {
                'id_type': _type.get('@id', 0),
                'type_name': get_normalized_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                                 'type_name',
                                                 _type.get('name', '')),
                'id_sale': id_sale,
                'sale_name': get_normalized_name(FRT_ROUTE_ROLE.PRDT_INFO,
                                                 'sale_name',
                                                 sale_info.get('name', '')),
            }

        one['out_of_stock'] = False #TODO get from user server
        order_items.append(one)

        item_invoice_info = {}
        for iv in item_info['invoice_info']:
            iv_item_info = ujson.loads(iv['invoice_item'])
            if iv_item_info:
                taxes = as_list(iv_item_info.get('tax', {}))
                iv['tax'] = sum([float(t['#text']) for t in taxes
                                 if t.get('@to_worldwide') == 'True'
                                    or t.get('@show') == 'True'])
                iv['tax_per_item'] = iv['tax'] / int(iv_item_info['qty'])
                iv['show_final_price'] = len(
                    [t for t in taxes if t.get('@show') == 'True']) > 0
            else:
                iv['tax'] = 0
                iv['tax_per_item'] = 0
                iv['show_final_price'] = False
            item_invoice_info[iv['shipment_id']] = iv

        for _shipment_info in item_info['shipment_info']:
            shipment_id = _shipment_info.get('shipment_id')
            if not shipment_id:
                # sth. wrong when create order
                continue
            shipping_list = _shipment_info.copy()
            shipping_list.update(item_invoice_info.get(shipment_id))

            shipping_list['item'] = order_items[-1]
            shipping_list['item']['quantity'] = shipping_list['shipping_list_quantity']
            shipping_list['status_name'] = SHIPMENT_STATUS.toReverseDict().get(
                                           int(shipping_list['status']))
            shipping_list['due_within'] = shipping_list['due_within'] or 1
            shipping_list['shipping_within'] = shipping_list['shipping_within'] or 7
            shipping_list['shipping_msg'] = get_shipping_msg(order_status,
                            order_created, shipping_list['shipping_date'],
                            shipping_list['shipping_within'])
            if shipment_id not in shipments:
                shipments[shipment_id] = []
            shipments[shipment_id].append(shipping_list)

    data = {
        'order_id': order_id,
        'order_created': order_created,
        'order_status': order_status,
        'status_name': get_order_status_msg(order_status),
        'user_name': user_name,
        'dest_user_name': dest_user_name,
        'first_name': user_profile.get('first_name') or '',
        'dest_addr': dest_addr,
        'shipments': shipments,
        'order_invoice_url': get_url_format(FRT_ROUTE_ROLE.ORDER_INVOICES)
                             % {'id_order': order_id},
    }
    return data

def get_shipping_msg(order_status, order_created,
                     shipping_date, shipping_period):
    if order_status == ORDER_STATUS.AWAITING_SHIPPING:
        expected_shipping_date = format_date(order_created,
                            shipping_period, '%d/%m/%Y')
        shipping_msg = _('Off schedule by : %(date)s') \
                       % {'date': expected_shipping_date}
    elif order_status == ORDER_STATUS.COMPLETED:
        shipping_msg = _('Shipped at : %(date)s') \
                       % {'date': format_epoch_time(shipping_date)}
    else:
        shipping_msg = ''
    return shipping_msg

def get_order_status_msg(status):
    return {
        ORDER_STATUS.PENDING: _('Waiting for confirmation'),
        ORDER_STATUS.AWAITING_PAYMENT: _('Awaiting payment'),
        ORDER_STATUS.AWAITING_SHIPPING: _('Awaiting shipment'),
        ORDER_STATUS.COMPLETED: _('Shipped'),
    }.get(status) or status

def get_err_msg(err):
    return {
        'INVALID_REQUEST': _('Invalid request.'),
        'SERVER_ERR': _('Server error.'),
        'DB_ERR': _('Server error.'),
        'ERR_EMAIL': _('Invalid email.'),
        'ERR_PASSWORD': _('Invalid password.'),
        'ERR_LOGIN': _('Invalid email or password.'),
        'INVALID_FIRST_NAME': _('Invalid first name.'),
        'INVALID_LAST_NAME': _('Invalid last name.'),
        'INVALID_COMPANY_TAX_ID': _('Invalid Company\'s Tax Identification '
                                    'or Registration Number'),
        'INVALID_PHONE_NUMBER': _('Invalid phone number.'),
        'INVALID_ADDRESS': _('Invalid address.'),
        'INVALID_CITY': _('Invalid city.'),
        'INVALID_POSTAL_CODE': _('Invalid postal code.'),
        'FAILED_PLACE_ORDER': _('Failed to place your order.'),
        'ERR_QUANTITY': _('Invalid quantity.'),
    }.get(err) or err

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

def send_reload_signal(pid):
    logging.info("Send reload signal...")
    os.kill(pid, signal.SIGHUP)

def generate_random_key():
    return uuid.uuid4()

def watching_invalidate_cache_list(pid):
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
                send_reload_signal(pid)
            redis_down = False

def get_client_ip(request):
    env = request.env
    try:
        return env['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    except KeyError:
        return env['REMOTE_ADDR']


ROUTE_NAME_MAPPING = {
    'type_name': normalize_name,
    'sale_name': normalize_name,
}

def get_thumbnail(img_url, width, height=None):
    if not img_url: return ""
    if not height: height = width
    size = width, height

    return get_thumbnail_url(img_url, size,
                      settings.FRONT_ROOT_URI,
                      settings.STATIC_FILES_PATH)

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
}

def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in text)

def html_escape_params(req, resp, params):
    for p in req._params:
        req._params[p] = html_escape(req._params[p])

def unescape_string(s):
    h = HTMLParser.HTMLParser()
    return h.unescape(s)

def gen_SID(num_bytes=16):
    return uuid.UUID(bytes=M2Crypto.m2.rand_bytes(num_bytes))

def gen_cookie_expiry(utc_expiry):
    return utc_expiry.strftime(EXPIRY_FORMAT)

def format_datetime(dt_str, tz_from='UTC', tz_to=settings.TIMEZONE):
    dt = parse_ts(dt_str)
    if dt is None:
        if dt_str:
            logging.error('Failed to format datetime: %s', dt_str)
        return dt_str
    return localize_datetime(dt, tz_from, tz_to
                             ).strftime('%Y-%m-%d %H:%M')

def countdown_time(dt_str):
    dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    now = datetime.datetime.strptime(format_datetime(datetime.datetime.utcnow()),
                                     '%Y-%m-%d %H:%M')
    days = hours = mins = total_seconds = 0
    if dt > now:
        delta = dt - now
        days = delta.days
        hours = delta.seconds / 3600
        mins = delta.seconds % 3600 / 60
        total_seconds = delta.total_seconds()
    return {'days': days, 'hours': hours, 'mins': mins,
            'total_seconds': total_seconds}

def refresh_time(dt_str):
    dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    now = datetime.datetime.strptime(format_datetime(datetime.datetime.utcnow()),
                                     '%Y-%m-%d %H:%M')
    hours = mins = total_seconds = 0
    if now > dt:
        delta = now - dt
        total_seconds = delta.total_seconds()
        hours = delta.total_seconds() / 3600
        mins = delta.total_seconds() % 3600 / 60
    return {'hours': hours, 'mins': mins,
            'total_seconds': total_seconds}

