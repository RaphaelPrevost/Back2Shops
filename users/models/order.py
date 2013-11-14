import logging
from datetime import datetime

from common.constants import SHIPMENT_STATUS
from settings import ORDERS_QUERY_LIMIT

from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from B2SUtils.db_utils import update
from models.sale import CachedSale
from models.shop import get_shop_id
from models.user import get_user_address
from models.user import get_user_phone_num
from models.user import get_user_profile


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


def _get_orders(conn, where=None, columns=None, order_by=None, limit=None,
                offset=None):
    order_by = order_by or ('confirmation_time', )
    orders = select(conn, 'orders', where=where, order=order_by,
                    columns=columns, limit=limit, offset=offset)
    return orders


def get_orders(conn, limit=None, offset=0):
    limit = limit or ORDERS_QUERY_LIMIT
    orders = _get_orders(conn, limit=limit, offset=offset)
    return orders


def get_orders_filter_by_confirmation_time(conn, start_time, end_time):
    orders = _get_orders(conn, where={'confirmation_time__>=': start_time,
                                      'confirmation_time__<': end_time})
    return orders


def get_orders_filter_by_user(conn, user_id):
    orders = _get_orders(conn, where={'id_user': user_id})
    return orders


def get_orders_filter_by_mother_brand(conn, mother_brand_id):
    query_str = '''
        SELECT id, id_user, confirmation_time
        FROM orders
        LEFT JOIN order_details ON order_details.id_order = order.id
        LEFT JOIN order_items ON order_items.id = order_details.id_item
        LEFT JOIN shops_shop ON shops_shop.id = order_items.id_shop
        WHERE order_items.mother_brand = %s
        ORDER BY confirmation_time
    '''
    orders = query(conn, query_str, [mother_brand_id, ])
    return orders


def _get_order_items(conn, order_id, mother_brand_id):
    # {'items': {item_1_id: {},
    #            item_2_id: {},
    #            ...}
    # }
    items = {'items': {}}
    fields_columns = [('item_id', 'order_items.id'),
                      ('quantity', 'quantity'),
                      ('sale_id', 'id_sale'),
                      ('shop_id', 'id_shop'),
                      ('price', 'price'),
                      ('name', 'name'),
                      ('picture', 'picture'),
                      ('description', 'description'),
                      ('copy_time', 'copy_time'),
                      ]
    if mother_brand_id is not None:
        query_str = (
            "SELECT %s FROM order_details "
            "LEFT JOIN order_items ON order_details.id_item = order_items.id "
            "LEFT JOIN shops_shop ON shops_shop.id = order_items.id_shop "
            "WHERE id_order=%%s AND id_shop=%%s"
            ) % ', '.join([x[1] for x in fields_columns])
        params = [order_id, mother_brand_id]
    else:
        query_str = (
            "SELECT %s FROM order_details "
            "LEFT JOIN order_items ON order_details.id_item = order_items.id "
            "WHERE id_order=%%s") % ', '.join([x[1] for x in fields_columns])
        params = [order_id, ]

    results_list = query(conn, query_str, params=params)

    for result in results_list:
        item_id = result[0]
        result = dict(zip([x[0] for x in fields_columns][1:], result[1:]))
        items['items'].update({item_id: result})

    return items


def get_order_detail(conn, order_id, mother_brand_id):
    columns = ['id', 'id_user', 'confirmation_time']
    results = select(conn, 'orders', where={'id': order_id}, columns=columns,
                     limit=1)
    if not results:
        return {}

    details = dict(zip(columns, results[0]))

    # details['user info']
    # user_info: {'address': {a1, a2, ...},
    #             'phone_num': {p1, p2, ...},
    #             'first_name': xxx,
    #             'last_name': xxx,
    #             ...
    # }
    user_id = details['id_user']
    user_info_dict = get_user_profile(conn, user_id)
    user_info_dict.update(get_user_address(conn, user_id))
    user_info_dict.update(get_user_phone_num(conn, user_id))
    details['user_info'] = user_info_dict

    # details['items']
    # items: {item_1_id: {xxx},
    #         item_2_id: {xxx},
    #         ...
    # }
    details.update(_get_order_items(conn, order_id, mother_brand_id))

    return details
