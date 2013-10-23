import logging
import ujson
from datetime import datetime
from common.constants import SHIPMENT_STATUS
from common.constants import BARCODE
from common.constants import BARCODE_VARIANT_ID
from common.constants import BARCODE_SALE_ID
from common.constants import BARCODE_SHOP
from common.db_utils import insert, select
from common.error import NotExistError
from common.redis_utils import get_redis_cli
from models.sale import CachedSale

def _create_order(conn, users_id):
    values = {'id_user': users_id}
    order_id = insert(conn, 'orders', values=values, returning='id')
    logging.info('order_create: id: %s, users_id: %s',
                 order_id, users_id)
    return order_id[0]

def _get_shop_by_upc(upc_shop):
    cli = get_redis_cli()
    return cli.get(BARCODE_SHOP % upc_shop)

def _create_order_item(conn, sale, id_variant, upc_shop=None):
    if upc_shop:
        shop_id = _get_shop_by_upc(upc_shop)
    else:
        shop_id = sale.get_shop_id()

    item_value = {
        'id_sale': sale.id,
        'id_variant': id_variant,
        'id_shop': shop_id,
        'price': sale.final_price(id_variant),
        'name': sale.whole_name(id_variant),
        'picture': sale.get_picture(),
        'description': sale.desc,
        'barcode': upc_shop or ''
    }
    item_id = insert(conn, 'order_items',
                     values=item_value, returning='id')
    logging.info('order_item create: item id: %s, values: %s',
                 item_id, item_value)
    return item_id[0]

def create_shipment(conn, id_order, addr_id):
    addr = select(conn, 'users_address', where={'id': addr_id})
    if not addr:
        raise NotExistError('Address %s not exist.' % addr_id)
    sm_values = {
        'id_order': id_order,
        'id_address': addr_id,
        #'id_phone': '?',
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

def _create_shipping_list(conn, id_item, sm_shipaddr_id, quantity, picture):
    shipping_value = {
        'id_item': id_item,
        'id_shipment': sm_shipaddr_id,
        'quantity': quantity,
        'picture': picture and ujson.dumps(picture) or '',
        }
    insert(conn, 'shipping_list', values=shipping_value)
    logging.info('shipping_list create: %s', shipping_value)

def create_pos_order(conn, users_id, upc_shop, order_items):
    order_id = _create_order(conn, users_id)
    for barcode, quantity in order_items:
        cli = get_redis_cli()
        key = BARCODE % barcode
        id_sale = cli.hget(key, BARCODE_SALE_ID)
        id_variant = cli.hget(key, BARCODE_VARIANT_ID)
        sale = CachedSale(id_sale).sale
        item_id = _create_order_item(conn, sale, id_variant, upc_shop)
        _create_order_details(conn, order_id, item_id, quantity)
    return order_id

def create_www_order(conn, users_id, shipaddr_id, billaddr_id, order_items):
    order_id = _create_order(conn, users_id)
    # create shipment for the new order's shipaddr_id, TODO: billaddr_id??
    sm_shipaddr_id = create_shipment(conn, order_id, shipaddr_id)

    for item in order_items:
        sale = CachedSale(item['id_sale']).sale
        item_id = _create_order_item(conn, sale, item['id_variant'])
        _create_order_details(conn, order_id, item_id, item['quantity'])
        _create_shipping_list(conn, item_id, sm_shipaddr_id, item['quantity'], sale.get_picture())

    return order_id


