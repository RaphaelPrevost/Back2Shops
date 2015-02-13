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


import settings
import logging
import ujson

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from common.error import UsersServerError
from countries.models import Country

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


def _populate_order_info(order):
    for id_order, order_detail in order.iteritems():
        search_options = []
        shipping_dest = order_detail['shipping_dest']
        country_code = shipping_dest['country']
        country = Country.objects.get(iso=country_code)
        shipping_dest['country_iso'] = country.iso
        shipping_dest['country_iso3'] = country.iso3
        shipping_dest['country_name'] = country.name
        shipping_dest['country_printable_name'] = country.printable_name
        shipping_dest['country_numcode'] = country.numcode

        search_options.append(shipping_dest['full_name'])
        search_options.append(shipping_dest['address'])
        search_options.append(shipping_dest['address2'])

        user_info = order_detail['user_info']
        search_options.append(user_info['email'])

        contact_phone = order_detail['contact_phone']
        search_options.append(contact_phone['phone_num'])

        order_items = order_detail['order_items']
        for id_item, item_detail in order_items:
            search_options.append(item_detail['name'])

        options = [item.lower() for item in search_options
                   if item != None and item != ""]
        order_detail['search_options'] = ' '.join(options)

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
        orders = ujson.loads(data)
        for order in orders:
            _populate_order_info(order)
        return orders
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


def remote_invoices(id_order, id_brand, id_shops):
    try:
        if isinstance(id_shops, list):
            id_shops = ujson.dumps(id_shops)

        uri = "%s?order=%s&brand=%s&shops=%s" % (
            settings.ORDER_INVOICES,
            id_order, id_brand, id_shops)

        data = get_from_remote(
            uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH
        )
        return data
    except Exception, e:
        logging.error('Failed to get order(id=%s) invoices from '
                      'usr servers: %s',
                      id_order, e, exc_info=True)
        raise UsersServerError


def remote_send_invoices(id_order, id_brand, id_shops):
    try:
        if isinstance(id_shops, list):
            id_shops = ujson.dumps(id_shops)

        query = {'order': id_order,
                 'brand': id_brand,
                 'shops': id_shops}

        data = get_from_remote(
            settings.ORDER_SEND_INVOICES,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            data=ujson.dumps(query),
            headers={'Content-Type': 'application/json'})
        return data
    except Exception, e:
        logging.error('Failed to send order(id=%s) invoices for: %s',
                      id_order, e, exc_info=True)
        raise UsersServerError


def send_new_shipment(id_order, id_shop, id_brand,
                      shipping_fee, handling_fee, content,
                      shipping_carrier, packing_status, tracking_name,
                      shipping_service=None, shipping_date=None,
                      tracking_num=None):
    if isinstance(content, list):
        content = ujson.dumps(content)

    try:
        data = {'action': 'create',
                'order': id_order,
                'shop': id_shop,
                'brand': id_brand,
                'handling_fee': handling_fee,
                'shipping_fee': shipping_fee,
                'content': content,
                'shipping_carrier': shipping_carrier,
                'packing_status': packing_status,
                'tracking_name': tracking_name,
                'shipping_service': shipping_service,
                'shipping_date': shipping_date,
                'tracking_num': tracking_num}

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
             'id_shop': id_shop,
             'content': content}, e, exc_info=True)
        raise UsersServerError

def send_update_shipment(id_shipment, id_shop, id_brand,
                         shipping_fee=None, handling_fee=None,
                         status=None, tracking_num=None, content=None,
                         shipping_date=None, tracking_name=None,
                         shipping_carrier=None):
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
        if tracking_name:
            data['tracking_name'] = tracking_name
        if shipping_carrier:
            data['shipping_carrier'] = shipping_carrier

        if not data:
            return

        data['shipment'] = id_shipment
        data['shop'] = id_shop
        data['brand'] = id_brand
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


def send_delete_shipment(id_shipment, id_shop, id_brand):
    try:
        data = {'action': 'delete',
                'shipment': id_shipment,
                'shop': id_shop,
                'brand': id_brand}
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

def remote_delete_order(id_order, id_brand, id_shops):
    try:
        if isinstance(id_shops, list):
            id_shops = ujson.dumps(id_shops)

        data = {'order': id_order,
                'brand': id_brand,
                'shops': id_shops}
        data = gen_encrypt_json_context(ujson.dumps(data),
                    settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
                    settings.PRIVATE_KEY_PATH)
        rst = get_from_remote(
            settings.ORDER_DELETE,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.USR],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return rst
    except Exception, e:
        logging.error('Failed to delete order %s,'
                      'error: %s',
                      {'id_order': id_order}, e, exc_info=True)
        raise UsersServerError
