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


import logging
import gevent
import ujson

from collections import defaultdict
from common.error import ErrorCode as E_C
from common.error import NotExistError
from common.error import UserError
from common.utils import push_order_confirming_event
from datetime import datetime
from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SUtils.base_actor import actor_to_dict
from B2SUtils.common import to_round
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import update
from B2SUtils.db_utils import select
from B2SProtocol.constants import INVOICE_STATUS
from models.actors.sale import CachedSale
from models.actors.shop import get_shop_id
from models.invoice import iv_to_sent_qty
from models.invoice import order_iv_sent_status
from models.shipments import decrease_stock
from models.shipments import get_shipments_by_order
from models.shipments import out_of_stock_errmsg
from models.shipments import posOrderShipments
from models.shipments import stock_req_params
from models.shipments import wwwOrderShipments
from models.stats_log import gen_bought_history
from models.user import get_user_dest_addr
from models.user import get_user_profile
from models.user import get_user_sel_phone_num


def _create_order(conn, users_id):
    values = {'id_user': users_id}
    order_id = insert(conn, 'orders', values=values, returning='id')
    logging.info('order_create: id: %s, users_id: %s',
                 order_id, users_id)

    return order_id[0]

def _create_order_shipment_detail(conn, id_order,
                                  id_shipaddr, id_billaddr,
                                  id_phone):

    values = {'id_order': id_order,
              'id_shipaddr': id_shipaddr,
              'id_billaddr': id_billaddr,
              'id_phone': id_phone,
              }
    insert(conn, 'order_shipment_details', values=values)
    logging.info('order_shipment_details item created:'
                 'values: %s' % values)

def _modify_order_shipment_detail(conn, id_order,
                                  id_shipaddr, id_billaddr,
                                  id_phone):

    values = {'id_shipaddr': id_shipaddr,
              'id_billaddr': id_billaddr,
              'id_phone': id_phone,
              }
    update(conn, 'order_shipment_details', values=values, where={'id_order': id_order})
    logging.info('order_shipment_details for order %s modified values: %s',
                 id_order, values)

def _create_order_item(conn, sale, id_variant, id_brand, upc_shop=None,
                       barcode=None, id_shop=None,
                       id_type=None,
                       id_weight_type=None,
                       id_price_type=None):
    if upc_shop:
        shop_id = get_shop_id(upc_shop)
    else:
        shop_id = id_shop

    item_value = {
        'id_sale': sale.id,
        'id_variant': id_variant,
        'id_brand': id_brand,
        'id_shop': shop_id or 0,
        'price': sale.final_price(id_variant, id_price_type or 0),
        'currency': sale.price.currency,
        'name': sale.whole_name(id_variant),
        'description': sale.desc,
        'weight_unit': sale.weight_unit,
    }
    external_id = sale.get_external_id(id_variant, id_type)
    main_picture = sale.get_main_picture(id_variant)
    if not main_picture:
        main_picture = sale.get_main_picture()
    if main_picture:
        item_value['picture'] = main_picture
    if barcode:
        item_value['barcode'] = barcode
    if id_type is not None:
        item_value['id_type'] = id_type
        if id_type:
            item_value['type_name'] = sale.get_weight_attr(id_type).name
    if id_weight_type is not None:
        item_value['id_weight_type'] = id_weight_type
    if id_price_type is not None:
        item_value['id_price_type'] = id_price_type
    if external_id is not None:
        item_value['external_id'] = external_id

    try:
        variant = sale.get_variant(id_variant)
        if variant:
            item_value['variant_detail'] = ujson.dumps(actor_to_dict(variant))
    except NotExistError:
        pass

    try:
        weight_detail = sale.get_weight_attr(id_weight_type)
        item_value['weight'] = weight_detail.weight.value
        item_value['weight_type_detail'] = ujson.dumps(actor_to_dict(weight_detail))
    except NotExistError:
        item_value['weight'] = sale.standard_weight

    item_value['item_detail'] = ujson.dumps(actor_to_dict(sale))

    item_id = insert(conn, 'order_items',
                     values=item_value, returning='id')
    logging.info('order_item create: item id: %s, values: %s',
                 item_id, item_value)
    return item_id[0]

def _create_order_details(conn, id_order, id_item, quantity):
    details_value = {
        'id_order': id_order,
        'id_item': id_item,
        'quantity': quantity
    }
    insert(conn, 'order_details', values=details_value)
    logging.info('order_details create: %s', details_value)

def _log_order(conn, users_id, id_order, sellers):
    for id_brand, shops in sellers.iteritems():
        for id_shop in shops:
            values = {'users_id': users_id,
                      'id_order': id_order,
                      'id_brand': id_brand,
                      'id_shop': id_shop
                      }
            insert(conn, 'orders_log', values=values)

def up_order_log(conn, id_order, sellers):
    for id_brand, shops in sellers.iteritems():
        for id_shop in shops:
            status = get_order_status(conn, id_order, id_brand, [id_shop])
            where = {'id_order': id_order,
                     'id_brand': id_brand,
                     'id_shop': id_shop}
            log = select(conn, 'orders_log', where=where)
            if log:
                log = log[0]
            else:
                continue
            v = None
            if status == ORDER_STATUS.PENDING:
                if log['pending_date'] is None:
                    v = {'pending_date': datetime.utcnow().date()}
            elif status == ORDER_STATUS.AWAITING_PAYMENT:
                if log['waiting_payment_date'] is None:
                    v = {'waiting_payment_date': datetime.utcnow().date()}
            elif status == ORDER_STATUS.AWAITING_SHIPPING:
                if log['waiting_shipping_date'] is None:
                    v = {'waiting_shipping_date': datetime.utcnow().date()}
            elif status == ORDER_STATUS.COMPLETED:
                if log['completed_date'] is None:
                    v = {'completed_date': datetime.utcnow().date()}
            if v is not None:
                where = {'id_order': id_order,
                         'id_brand': id_brand,
                         'id_shop': id_shop}
                update(conn, 'orders_log', values=v, where=where)


def create_order(conn, users_id, telephone_id, order_items,
                 upc_shop=None, shipaddr=None, billaddr=None,
                 user_info=None, chosen_gifts=None):
    order_id = _create_order(conn, users_id)
    _create_order_shipment_detail(conn, order_id, shipaddr,
                                  billaddr, telephone_id)

    sellers = defaultdict(set)
    id_sales = []
    for item in order_items:
        sale = CachedSale(item['id_sale']).sale
        item_id = _create_order_item(conn, sale, item['id_variant'],
                                     sale.brand.id,
                                     upc_shop=upc_shop,
                                     barcode=item.get('barcode', None),
                                     id_shop=item['id_shop'],
                                     id_type=item.get('id_type', None),
                                     id_price_type=item.get('id_price_type', None),
                                     id_weight_type=item.get('id_weight_type', None))
        # populate id_order_item into order params, it will be
        # used when create shipping list.
        item['id_order_item'] = item_id
        id_sales.append(sale.id)
        _create_order_details(conn, order_id, item_id, item['quantity'])
        sellers[sale.brand.id].add(item['id_shop'])

    gevent.spawn(gen_bought_history, users_id, id_sales)
    _log_order(conn, users_id, order_id, sellers)

    if upc_shop is None:
        wwwOrderShipments(conn,
                          order_id,
                          order_items,
                          shipaddr,
                          users_id).create()
    else:
        posOrderShipments(conn,
                          order_id,
                          order_items,
                          None,
                          users_id).create()

    up_order_log(conn, order_id, sellers)

    if not _order_need_confirmation(conn, order_id):
        params = []
        shipments = get_shipments_by_order(conn, order_id)
        for s in shipments:
            params += stock_req_params(conn, s['id'])
        success, errmsg = decrease_stock(params)
        if not success:
            raise UserError(E_C.OUT_OF_STOCK[0],
                            out_of_stock_errmsg(errmsg))

    for brand, shops in sellers.iteritems():
        try:
            if _order_need_confirmation(conn, order_id, brand):
                push_order_confirming_event(conn, order_id, brand)
        except Exception, e:
            logging.error('confirming_event_err: %s, '
                          'order_id: %s, '
                          'brand: %s',
                          e, order_id, brand, exc_info=True)

    from models.coupon import apply_appliable_coupons
    apply_appliable_coupons(conn, users_id, order_id,
                            user_info, chosen_gifts)

    return order_id

def delete_order(conn, order_id, brand_id, shops_id):
    fields, columns = zip(*(ORDER_ITEM_FIELDS_COLUMNS))
    query_str = """
        SELECT %s
          FROM orders
     LEFT JOIN order_details
            ON order_details.id_order = orders.id
     LEFT JOIN order_items
            ON order_items.id = order_details.id_item
         WHERE orders.id = %%s
      ORDER BY confirmation_time, order_items.id
    """ % (', '.join(columns))
    results = query(conn, query_str, params=[order_id])

    allowed = True
    for result in results:
        order_item = dict(zip(fields, result))
        if (order_item['brand_id'] != int(brand_id) or
            order_item['shop_id'] not in shops_id):
            allowed = False
            break

    if allowed:
        update(conn, 'orders',
               values={'valid': False},
               where={'id': order_id})

        from models.coupon import cancel_coupon_for_order
        cancel_coupon_for_order(conn, order_id)

    return allowed


def modify_order(conn, users_id, order_id, telephone_id, order_items,
                 shipaddr, billaddr):
    _modify_order_shipment_detail(conn, order_id, shipaddr, billaddr, telephone_id)
    shipments = get_shipments_by_order(conn, order_id)
    shipment_ids = [s['id'] for s in shipments]
    wwwOrderShipments(conn,
                      order_id,
                      order_items,
                      shipaddr,
                      users_id).update(shipment_ids)
    return int(order_id)

def update_shipping_fee(conn, id_shipment, id_postage, shipping_fee):
    try:
        shipping_fee = to_round(shipping_fee)
        update(conn, 'shipping_supported_services',
               values={'id_postage': id_postage},
               where={'id_shipment': id_shipment})
        update(conn, 'shipping_fee',
               values={'shipping_fee': shipping_fee},
               where={'id_shipment': id_shipment})
        conn.commit()
        logging.info('update_shipping_fee:'
                     'id_postage: %s, '
                     'shipping_fee: %s, '
                     'for shipment: %s,'
                     % (id_postage, shipping_fee, id_shipment))
    except Exception, e:
        conn.rollback()
        logging.error('update_shipping_fee err: %s, '
                      'args: id_shipment: %s,'
                      'id_postage: %s, '
                      'shipping_fee: %s'
                      % (e, id_shipment, id_postage, shipping_fee),
                      exc_info=True)
        raise


ORDER_FIELDS_COLUMNS = [('order_id', 'orders.id'),
                        ('user_id', 'id_user'),
                        ('confirmation_time', 'confirmation_time'),
                        ('valid', 'valid'),
                        ]
ORDER_SHIPMENT_COLUMNS = [('id_shipaddr', 'id_shipaddr'),
                         ('id_phone', 'id_phone'),
                        ]
ORDER_ITEM_FIELDS_COLUMNS = [('item_id', 'order_items.id'),
                             ('quantity', 'quantity'),
                             ('sale_id', 'id_sale'),
                             ('shop_id', 'id_shop'),
                             ('brand_id', 'id_brand'),
                             ('id_variant', 'id_variant'),
                             ('price', 'price'),
                             ('name', 'name'),
                             ('picture', 'picture'),
                             ('description', 'description'),
                             ('copy_time', 'copy_time'),
                             ('barcode', 'barcode'),
                             ('id_weight_type', 'id_weight_type'),
                             ('id_price_type', 'id_price_type'),
                             ('id_type', 'id_type'),
                             ('type_name', 'type_name'),
                             ('external_id', 'order_items.external_id'),
                             ('currency', 'order_items.currency'),
                             ('weight', 'order_items.weight'),
                             ('weight_unit', 'order_items.weight_unit'),
                             ('sel_variant', 'order_items.variant_detail'),
                             ('sel_weight_type', 'order_items.weight_type_detail'),
                             ('item_detail', 'order_items.item_detail'),
                             ('modified_by_coupon', 'order_items.modified_by_coupon'),
                             ]


def _get_shipment_info_for_order_item(conn, item_id):
    fields, columns = zip(*[('shipment_id', 'shipments.id'),
                            ('status', 'shipments.status'),
                            ('handling_fee', 'handling_fee'),
                            ('shipping_fee', 'shipping_fee'),
                            ('shipping_date', 'shipping_date'),
                            ('shipping_list_quantity', 'quantity'),
                            ('packing_quantity', 'packing_quantity'),
                         ])
    query_str = (
        "SELECT %s FROM shipping_list "
     "LEFT JOIN shipments "
            "ON shipments.id = shipping_list.id_shipment "
     "LEFT JOIN shipping_fee "
            "ON shipments.id = shipping_fee.id_shipment "
         "WHERE id_item = %%s "
      "ORDER BY shipping_list.id_shipment, shipping_list.id_item")\
                % ', '.join(columns)

    results = query(conn, query_str, params=[item_id, ])
    return [dict(zip(fields, r)) for r in results]

def _get_invoice_info_for_order_item(conn, item_id):
    fields, columns = zip(*[('shipment_id', 'shipments.id'),
                            ('total_amount', 'amount_due'),
                            ('currency', 'currency'),
                            ('due_within', 'due_within'),
                            ('shipping_within', 'shipping_within'),
                            ('invoice_item', 'invoice_items'),
                         ])
    query_str = (
        "SELECT %s FROM shipping_list "
     "LEFT JOIN shipments "
            "ON shipments.id = shipping_list.id_shipment "
     "LEFT JOIN invoices "
            "ON shipments.id = invoices.id_shipment "
         "WHERE id_item = %%s "
      "ORDER BY shipping_list.id_shipment, shipping_list.id_item")\
                % ', '.join(columns)

    results = query(conn, query_str, params=[item_id, ])
    results = [dict(zip(fields, r)) for r in results]
    for r in results:
        if r['invoice_item']:
            items_dict = dict([(i['@id'], i)
                               for i in ujson.loads(r['invoice_item'])])
            r['invoice_item'] = ujson.dumps(items_dict.get(str(item_id)) or {})
        else:
            r['invoice_item'] = ujson.dumps({})
    return results

def _get_order_shipments_status(conn, id_order, id_brand=None, id_shops=None):
    query_str = ("SELECT status "
                   "FROM shipments ")
    where = 'WHERE id_order = %s '
    where_v = [id_order]
    if id_brand:
        where += 'and id_brand = %s '
        where_v.append(id_brand)
    if id_shops:
        where += 'and id_shop in %s'
        where_v.append(tuple(id_shops))

    query_str += where
    rst = query(conn, query_str, where_v)
    return [item[0] for item in rst]

def _get_order_invoice_status(conn, id_order, id_brand=None, id_shops=None):
    query_str = ("SELECT iv.status FROM invoices as iv ")

    if id_brand is not None or id_shops:
        query_str += "JOIN shipments as sp ON iv.id_shipment = sp.id "

    where = 'where iv.id_order = %s '
    where_v = [id_order,]

    if id_brand is not None:
        where += 'and sp.id_brand = %s '
        where_v.append(int(id_brand))
    if id_shops:
        where += 'and sp.id_shop in %s '
        where_v.append(tuple(id_shops))

    query_str += where
    rst = query(conn, query_str, where_v)
    return [item[0] for item in rst]

def _order_need_confirmation(conn, id_order, id_brand=None, id_shops=None):
    query_str = "select 1 from shipments where id_order=%s and status=%s"
    params = [id_order, SHIPMENT_STATUS.CONFIRMING]
    if id_brand:
        query_str += " and id_brand=%s"
        params.append(id_brand)
    if id_shops:
        query_str += 'and id_shop in %s '
        params.append(tuple(id_shops))
    confirming_items = query(conn, query_str, params=params)
    return confirming_items and len(confirming_items) > 0

def _all_order_items_packed(conn, id_order, id_brand=None, id_shops=None):
    item_qtt_sql = ("SELECT sum(quantity) "
                      "FROM order_details as od ")
    where = 'WHERE od.id_order=%s '
    where_v = [id_order, ]
    if id_brand is not None or id_shops is not None:
        item_qtt_sql += 'JOIN order_items as oi on od.id_item = oi.id '
    if id_brand is not None:
        where += 'and oi.id_brand = %s '
        where_v.append(id_brand)
    if id_shops:
        where += 'and oi.id_shop in %s '
        where_v.append(tuple(id_shops))

    item_qtt_sql += where
    item_qtt = query(conn, item_qtt_sql, where_v)[0][0]

    grouped_qtt_sql = ("SELECT sum(spl.packing_quantity) "
                         "FROM shipping_list as spl "
                         "JOIN shipments as sp "
                           "ON spl.id_shipment = sp.id ")

    where = "WHERE sp.id_order = %s AND sp.status <> %s "
    where_v = [id_order, SHIPMENT_STATUS.DELETED]
    if id_brand is not None:
        where += "and sp.id_brand = %s "
        where_v.append(id_brand)
    if id_shops:
        where += 'and sp.id_shop in %s '
        where_v.append(tuple(id_shops))
    grouped_qtt_sql += where

    packed_qtt = query(conn, grouped_qtt_sql, where_v)[0][0]
    return item_qtt == packed_qtt

def get_order_status(conn, order_id, id_brand=None, id_shops=None):
    """
    There is 4 status.
    Pending order is the initial status.
    When all the the shipments are created and matching invoices as well, the
    order becomes "awaiting payment".
    When all the invoices are paid, the order becomes "awaiting shipping".
    When the merchant has set the status of all shipments as sent, the order
    is "completed".
    """
    if id_shops and not isinstance(id_shops, list):
        id_shops = [id_shops]

    if _order_need_confirmation(conn, order_id, id_brand, id_shops):
        return ORDER_STATUS.PENDING
    if not _all_order_items_packed(conn, order_id, id_brand, id_shops):
        return ORDER_STATUS.PENDING

    shipment_status_set = set(_get_order_shipments_status(
        conn, order_id, id_brand, id_shops))
    invoice_status_set = set(_get_order_invoice_status(
        conn, order_id, id_brand, id_shops))

    if shipment_status_set == set([SHIPMENT_STATUS.FETCHED]):
        return ORDER_STATUS.COMPLETED

    if (invoice_status_set == set([INVOICE_STATUS.INVOICE_PAID]) and
            shipment_status_set == set([SHIPMENT_STATUS.DELIVER])):
        return ORDER_STATUS.COMPLETED

    if (invoice_status_set == set([INVOICE_STATUS.INVOICE_PAID]) and
            shipment_status_set != set([SHIPMENT_STATUS.DELIVER])):
        return ORDER_STATUS.AWAITING_SHIPPING

    if (len(invoice_status_set) > 0
            and invoice_status_set != set([INVOICE_STATUS.INVOICE_PAID])):
        return ORDER_STATUS.AWAITING_PAYMENT

    return ORDER_STATUS.PENDING

def _get_order_carrier_ids(conn, order_id):
    query_str = (
        "SELECT id_postage, supported_services FROM shipments "
          "JOIN shipping_supported_services "
            "ON shipments.id = shipping_supported_services.id_shipment "
         "WHERE id_order = %s "
           "AND id_postage is not null")
    results = query(conn, query_str, params=[order_id, ])
    return [str(ujson.loads(s_mapping)[str(s_id)])
            for s_id, s_mapping in results]

def _get_paid_time_list(conn, status, order_id):
    if status == ORDER_STATUS.COMPLETED:
        fields, columns = zip(*[('shop_id', 'id_shop'),
                                ('timestamp', 'invoice_status.timestamp')])
        query_str = (
            "SELECT %s FROM shipments "
         "LEFT JOIN invoices "
                "ON shipments.id = invoices.id_shipment "
         "LEFT JOIN invoice_status "
                "ON invoices.id = invoice_status.id_invoice "
             "WHERE shipments.id_order = %%s "
               "AND invoice_status.status = %%s ") \
                    % ', '.join(columns)
    else:
        fields, columns = zip(*[('shop_id', 'id_shop'),
                                ('timestamp', 'invoices.update_time')])
        query_str = (
            "SELECT %s FROM shipments "
         "LEFT JOIN invoices "
                "ON shipments.id = invoices.id_shipment "
             "WHERE shipments.id_order = %%s "
               "AND invoices.status = %%s ") \
                    % ', '.join(columns)
    results = query(conn, query_str, params=[order_id,
                                             INVOICE_STATUS.INVOICE_PAID])
    return [dict(zip(fields, r)) for r in results]


def _update_extra_info_for_order_item(conn, item_id, order_item):
    order_item.update(
        {'shipment_info': _get_shipment_info_for_order_item(conn, item_id),
         'invoice_info': _get_invoice_info_for_order_item(conn, item_id),
         })


def get_orders_list(conn, brand_id, shops_id=None,
                    users_id=None, limit=None, offset=None):
    fields, columns = zip(*(ORDER_FIELDS_COLUMNS +
                            ORDER_SHIPMENT_COLUMNS +
                            ORDER_ITEM_FIELDS_COLUMNS))

    filter_where = "where orders.valid and order_items.id_brand=%s "
    params = [brand_id]
    if users_id:
        filter_where += "and orders.id_user=%s "
        params.append(users_id)
    elif shops_id:
        filter_where += "and order_items.id_shop in %s "
        params.append(tuple(shops_id))

    order_by = "ORDER BY confirmation_time, order_items.id "
    if users_id:
        order_by = "ORDER BY confirmation_time desc, orders.id desc "

    limit_offset = ""
    if limit:
        limit_offset += "limit %s "
        params.append(limit)
    if offset:
        limit_offset += "offset %s"
        params.append(offset)

    query_str = """
        SELECT %s
          FROM orders
     LEFT JOIN order_details
            ON order_details.id_order = orders.id
     LEFT JOIN order_shipment_details
            ON order_shipment_details.id_order = orders.id
     LEFT JOIN order_items
            ON order_items.id = order_details.id_item
            %s
            %s
            %s
    """ % (', '.join(columns), filter_where, order_by, limit_offset)
    results = query(conn, query_str, params=params)

    orders_dict = {}
    sorted_order_ids = []
    for result in results:
        order_item = dict(zip(fields, result))

        order_id = order_item.pop('order_id')
        if order_id not in orders_dict:
            id_user = order_item.pop('user_id')
            id_shipaddr = order_item.pop('id_shipaddr')
            id_phone = order_item.pop('id_phone')
            orders_dict[order_id] = {
                'user_info': get_user_profile(conn, id_user),
                'user_id': id_user,
                'confirmation_time': order_item.pop('confirmation_time'),
                'thumbnail_img': order_item['picture'], # use the first
                # order item's picture as order's thumbnail image
                'shipping_dest': get_user_dest_addr(conn, id_user, id_shipaddr),
                'contact_phone': get_user_sel_phone_num(conn, id_user, id_phone),
                'order_items': [],
                'shop_ids': []}
        item_id = order_item.pop('item_id')
        _update_extra_info_for_order_item(conn, item_id, order_item)
        orders_dict[order_id]['order_items'].append((item_id, order_item))
        orders_dict[order_id]['shop_ids'].append(order_item['shop_id'])

        if order_id not in sorted_order_ids:
            sorted_order_ids.append(order_id)

    for order_id, order in orders_dict.iteritems():
        order['order_items'] = _sort_order_items(order['order_items'])
        order['order_status'] = get_order_status(conn, order_id, brand_id, shops_id)
        if order['order_status'] > ORDER_STATUS.AWAITING_PAYMENT:
            order['paid_time_info'] = _get_paid_time_list(
                conn, order['order_status'], order_id)
        if order['order_status'] == ORDER_STATUS.PENDING:
            order['iv_sent_status'] = order_iv_sent_status(conn,
                                                           order_id,
                                                           brand_id,
                                                           shops_id)
            order['iv_to_sent_qty'] = iv_to_sent_qty(conn,
                                                     order_id,
                                                     brand_id,
                                                     shops_id)
        order['shop_ids'] = list(set(order['shop_ids']))
        order['carrier_ids'] = list(set(_get_order_carrier_ids(conn, order_id)))

    orders = []
    for order_id in sorted_order_ids:
        orders.append({order_id: orders_dict[order_id]})
    return orders

def _sort_order_items(item_tuple_list):
    _item_key = lambda item_id, item: ujson.dumps({
        'id_sale': item_id,
        "id_variant": item["id_variant"],
        "id_price_type": item["id_price_type"],
        "id_type": item["id_type"],
    })

    fakes = {}
    normal_items = []
    for item_id, item in item_tuple_list:
        if item_id and item['price'] < 0:
            if _item_key(item_id, item) not in fakes:
                fakes[_item_key(item_id, item)] = []
            fakes[_item_key(item_id, item)].append((item_id, item))
        else:
            normal_items.append((item_id, item))

    results = []
    for item_id, item in normal_items:
        results.append((item_id, item))
        _key = _item_key(item_id, item)
        if _key in fakes:
            results += fakes.pop(_key)
    for items in fakes.values():
        results += items
    return results

def _get_order_items(conn, order_id, brand_id, shops_id=None):
    # {'order_items': [item_1_id: {},
    #                  item_2_id: {},
    #                  ...]
    # }
    items = {'order_items': []}
    results_list = get_order_items(conn, order_id)
    for order_item in results_list:
        if shops_id and order_item['shop_id'] not in shops_id:
            continue

        if order_item['brand_id'] != int(brand_id):
            continue

        item_id = order_item.pop('item_id')
        _update_extra_info_for_order_item(conn, item_id, order_item)
        items['order_items'].append((item_id, order_item))
    items['order_items'] = _sort_order_items(items['order_items'])
    return items

def get_order_items_by_id(conn, items_id):
    if not isinstance(items_id, list):
        items_id = [items_id]
    q = ("SELECT * "
           "FROM order_items "
          "WHERE id in %s")
    r = query(conn, q, [tuple(items_id)])
    return r

def get_order_items(conn, order_id):
    fields, columns = zip(*ORDER_ITEM_FIELDS_COLUMNS)
    query_str = ("SELECT %s "
                   "FROM order_details "
              "LEFT JOIN order_items "
                     "ON order_details.id_item = order_items.id "
                  "WHERE id_order = %%s") % ', '.join(columns)
    results_list = query(conn, query_str, params=[order_id, ])
    order_items = []
    for result in results_list:
        order_items.append(dict(zip(fields, result)))
    return order_items

def get_order_detail(conn, order_id, brand_id, shops_id=None):
    fields, columns = zip(*(ORDER_FIELDS_COLUMNS +
                            ORDER_SHIPMENT_COLUMNS))
    query_str = ("SELECT %s "
                   "FROM orders "
              "LEFT JOIN order_shipment_details "
                     "ON orders.id = order_shipment_details.id_order "
                  "WHERE id_order = %%s") % ', '.join(columns)
    results = query(conn, query_str, params=[order_id, ])
    if not results:
        return {}
    details = dict(zip(fields, results[0]))

    # details['user info']
    # user_info: {'address': {a1, a2, ...},
    #             'phone_num': {p1, p2, ...},
    #             'first_name': xxx,
    #             'last_name': xxx,
    #             ...
    # }

    details['user_info'] = get_user_profile(conn, details['user_id'])

    # details['order_items']
    # order_items: [item_1_id: {xxx},
    #               item_2_id: {xxx},
    #               ...
    # ]
    order_items = _get_order_items(conn, order_id, brand_id, shops_id)
    details.update(order_items)
    details.update({
        'thumbnail_img': order_items['order_items'][0][1]['picture']
                         if len(order_items['order_items']) > 0 else '',
        'shipping_dest': get_user_dest_addr(conn, details['user_id'],
                                            details['id_shipaddr']),
        'order_status': get_order_status(conn, order_id, brand_id, shops_id)})
    return details

def user_accessable_order(conn, id_order, id_user):
    query_str = ("SELECT id_user "
                   "FROM orders "
                  "WHERE id = %s")

    r = query(conn, query_str, (id_order,))
    if not r:
        return False
    else:
        return int(r[0][0]) == int(id_user)

def order_exist(conn, id_order):
    query_str = ("SELECT * "
                   "FROM orders "
                  "WHERE id = %s")

    r = query(conn, query_str, (id_order,))
    return True if r else False

def order_item_exist(conn, id_sale, id_variant, id_shop,
                     id_weight_type, id_price_type, quantity):

    query_str = ("SELECT oi.id "
                   "FROM order_items as oi "
                   "JOIN order_details as od "
                     "ON oi.id=od.id_item "
                  "WHERE oi.id_sale = %s "
                    "AND oi.id_variant = %s "
                    "AND oi.id_shop = %s "
                    "AND oi.id_weight_type = %s "
                    "AND oi.id_price_type = %s "
                    "AND od.quantity < %s"
                )

    r = query(conn, query_str, (id_sale, id_variant, id_shop,
                                id_weight_type, id_price_type,
                                quantity))
    if not r:
        return False
    else:
        return r[0][0]

ORDER_FIELDS = ['id', 'id_user', 'confirmation_time', 'id_shipaddr',
                'id_billaddr', 'id_phone']
def get_order(conn, id_order, id_user=None):
    where = "WHERE id = %s " % id_order
    if id_user:
        where += "AND id_user = %s" % id_user

    sql = ("SELECT %(fields)s "
             "FROM orders as o "
             "JOIN order_shipment_details as osd "
               "ON o.id = osd.id_order "
        "%(where)s "
        % {'fields': ', '.join(ORDER_FIELDS),
            'where': where})
    r = query(conn, sql)
    return len(r) > 0 and dict(zip(ORDER_FIELDS, r[0])) or None

def order_item_quantity(conn, id_item):
    query_str = ("SELECT quantity "
                   "FROM order_details "
                  "WHERE order_details.id_item = %s ")

    r = query(conn, query_str, (id_item, ))
    return r and r[0][0] or None
