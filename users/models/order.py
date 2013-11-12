import logging
from datetime import datetime
from common.constants import SHIPMENT_STATUS
from models.sale import CachedSale
from models.shop import get_shop_id
from B2SUtils.db_utils import insert, update, query

def _create_order(conn, users_id):
    values = {'id_user': users_id}
    order_id = insert(conn, 'orders', values=values, returning='id')
    logging.info('order_create: id: %s, users_id: %s',
                 order_id, users_id)
    return order_id[0]

def _create_order_item(conn, sale, id_variant, upc_shop=None,
                       barcode=None, id_shop=None):
    if upc_shop:
        shop_id = get_shop_id(upc_shop)
    else:
        shop_id = id_shop

    item_value = {
        'id_sale': sale.id,
        'id_variant': id_variant,
        'id_shop': shop_id,
        'price': sale.final_price(id_variant),
        'name': sale.whole_name(id_variant),
        'description': sale.desc,
        'barcode': upc_shop or ''
    }
    main_picture = sale.get_main_picture()
    if main_picture:
        item_value['picture'] = main_picture
    if barcode:
        item_value['barcode'] = barcode

    item_id = insert(conn, 'order_items',
                     values=item_value, returning='id')
    logging.info('order_item create: item id: %s, values: %s',
                 item_id, item_value)
    return item_id[0]

def create_shipment(conn, id_order, addr_id, id_phone):
    sm_values = {
        'id_order': id_order,
        'id_address': addr_id,
        'id_phone': id_phone,
        #'id_postage': '?',
        #'mail_tracking_num': '?',
        'status': SHIPMENT_STATUS.PACKING,
        #'shipping_fee': '?',
        'timestamp': datetime.utcnow(),
    }
    sm_id = insert(conn, 'shipments', values=sm_values, returning='id')
    logging.info('shipment create: id: %s, values: %s',
                 sm_id[0], sm_values)
    return sm_id[0]

def _create_order_details(conn, id_order, id_item, quantity):
    details_value = {
        'id_order': id_order,
        'id_item': id_item,
        'quantity': quantity
    }
    insert(conn, 'order_details', values=details_value)
    logging.info('order_details create: %s', details_value)

def _create_shipping_list(conn, id_item, quantity,
                          id_shipment=None, picture=None):
    shipping_value = {
        'id_item': id_item,
        'quantity': quantity,
        }

    if id_shipment:
        shipping_value['id_shipment'] = id_shipment
    if picture:
        shipping_value['picture'] = picture

    insert(conn, 'shipping_list', values=shipping_value)
    logging.info('shipping_list create: %s', shipping_value)

def create_order(conn, users_id, telephone_id, order_items,
                 upc_shop=None, shipaddr=None, billaddr=None):
    order_id = _create_order(conn, users_id)
    for order in order_items:
        sale = CachedSale(order['id_sale']).sale
        item_id = _create_order_item(conn, sale, order['id_variant'],
                                     upc_shop=upc_shop,
                                     barcode=order.get('barcode', None))
        _create_order_details(conn, order_id, item_id, order['quantity'])
    return order_id

def update_shipping_fee(conn, id_shipment, id_postage, shipping_fee):
    try:
        values={'id_postage': id_postage,
                'shipping_fee': shipping_fee}
        rst = update(conn, 'shipments',
               values=values,
               where={'id': id_shipment},
               returning='id')
        conn.commit()
        logging.info('update_shipping_fee:'
                     'id_order: %s,'
                     'values: %s, '
                     'for shipment: %s,'
                     % (id_shipment, values, rst))
    except Exception, e:
        logging.error('update_shipping_fee err: %s, '
                      'args: id_order: %s,'
                      'id_postage: %s, '
                      'shipping_fee: %s'
                      % (e, id_shipment, id_postage, shipping_fee), exc_info=True)
        raise
