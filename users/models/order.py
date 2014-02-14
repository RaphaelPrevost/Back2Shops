import logging

from common.constants import INVOICE_STATUS
from common.constants import ORDER_STATUS

from B2SProtocol.constants import SHIPMENT_STATUS
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from B2SUtils.db_utils import update
from models.sale import CachedSale
from models.shipments import wwwOrderShipments
from models.shipments import posOrderShipments
from models.shop import get_shop_id
from models.user import get_user_profile


def _create_order(conn, users_id):
    values = {'id_user': users_id}
    order_id = insert(conn, 'orders', values=values, returning='id')
    logging.info('order_create: id: %s, users_id: %s',
                 order_id, users_id)
    return order_id[0]


def _create_order_item(conn, sale, id_variant, upc_shop=None,
                       barcode=None, id_shop=None,
                       id_weight_type=None,
                       id_price_type=None):
    if upc_shop:
        shop_id = get_shop_id(upc_shop)
    else:
        shop_id = id_shop

    item_value = {
        'id_sale': sale.id,
        'id_variant': id_variant,
        'id_shop': shop_id,
        'price': sale.final_price(id_variant, id_price_type or 0),
        'name': sale.whole_name(id_variant),
        'description': sale.desc,
    }
    main_picture = sale.get_main_picture()
    if main_picture:
        item_value['picture'] = main_picture
    if barcode:
        item_value['barcode'] = barcode
    if id_weight_type is not None:
        item_value['id_weight_type'] = id_weight_type
    if id_price_type is not None:
        item_value['id_price_type'] = id_price_type

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



def create_order(conn, users_id, telephone_id, order_items,
                 upc_shop=None, shipaddr=None, billaddr=None):
    order_id = _create_order(conn, users_id)
    for order in order_items:
        sale = CachedSale(order['id_sale']).sale
        item_id = _create_order_item(conn, sale, order['id_variant'],
                                     upc_shop=upc_shop,
                                     barcode=order.get('barcode', None),
                                     id_shop=order['id_shop'],
                                     id_price_type=order.get('id_price_type', None),
                                     id_weight_type=order.get('id_weight_type', None))
        # populate id_order_item into order params, it will be
        # used when create shipping list.
        order['id_order_item'] = item_id
        _create_order_details(conn, order_id, item_id, order['quantity'])
    if upc_shop is None:
        wwwOrderShipments(conn,
                          order_id,
                          order_items,
                          telephone_id,
                          shipaddr,
                          users_id).create()
    else:
        posOrderShipments(conn,
                          order_id,
                          order_items,
                          telephone_id,
                          None,
                          users_id).create()

        # TODO: Create fake shipments for posOrder items.
        pass

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


ORDER_FIELDS_COLUMNS = [('order_id', 'orders.id'),
                        ('user_id', 'id_user'),
                        ('confirmation_time', 'confirmation_time'),
                        ]
ORDER_ITEM_FIELDS_COLUMNS = [('item_id', 'order_items.id'),
                             ('quantity', 'quantity'),
                             ('sale_id', 'id_sale'),
                             ('shop_id', 'id_shop'),
                             ('brand_id', 'id_variant'),
                             ('price', 'price'),
                             ('name', 'name'),
                             ('picture', 'picture'),
                             ('description', 'description'),
                             ('copy_time', 'copy_time'),
                             ('barcode', 'barcode'),
                             ]


def _valid_sale_brand(sale_id, brand_id):
    if int(brand_id) == 0:
        return True

    sale = CachedSale(sale_id).sale
    return sale and sale.brand and int(sale.brand.id) == int(brand_id)


def _get_shipment_info_for_order_item(conn, item_id):
    shipment_info = {}
    fields, columns = zip(*[('address_id', 'id_address'),
                            ('phone_id', 'id_phone'),
                            ('status', 'status'),
                            ('shipping_fee', 'shipping_fee'),
                            ('shipping_list_quantity', 'quantity')])
    query_str = (
        "SELECT %s FROM shipping_list "
        "LEFT JOIN shipments ON shipments.id = shipping_list.id_shipment "
        "WHERE id_item = %%s") % ', '.join(columns)

    results = query(conn, query_str, params=[item_id, ])
    assert len(results) <= 1, 'One item has more than one shipping_list?'
    if not results:
        return shipment_info
    shipment_info = dict(zip(fields, results[0]))

    # get shipment address info
    address_columns = ['addr_type', 'address', 'city', 'postal_code',
                       'country_code', 'province_code', 'address_desp']
    address_results = select(conn, 'users_address', columns=address_columns,
                             where={'id': shipment_info.pop('address_id')})
    if address_results:
        address_info = dict(zip(address_columns, address_results[0]))
        shipment_info.update({'shipment_address_info': address_info})

    # get shipment phone info
    phone_columns = ['country_num', 'phone_num', 'phone_num_desp']
    phone_results = select(conn, 'users_phone_num', columns=phone_columns,
                           where={'id': shipment_info.pop('phone_id')})
    if phone_results:
        phone_info = dict(zip(phone_columns, phone_results[0]))
        shipment_info.update({'shipment_phone_info': phone_info})

    return shipment_info


def _get_invoice_info_for_order_item(conn, item_id):
    # not implemented yet.
    return {}


def _get_order_status(order_items_list):
    """
    There is 4 status.
    Pending order is the initial status.
    When all the the shipments are created and matching invoices as well, the
    order becomes "awaiting payment".
    When all the invoices are paid, the order becomes "awaiting shipping".
    When the merchant has set the status of all shipments as sent, the order
    is "completed".
    """
    shipment_status_set = set()
    invoice_status_set = set()
    for order_item_dict in order_items_list:
        for item_id, item_info in order_item_dict.iteritems():
            shipment_status = item_info['shipment_info'].get('status', 0)
            shipment_status_set.add(shipment_status)

            invoice_status = item_info['invoice_info'].get('status', 0)
            invoice_status_set.add(invoice_status)

    if (invoice_status_set == set([INVOICE_STATUS.INVOICE_PAID]) and
            shipment_status_set == set([SHIPMENT_STATUS.DELIVER])):
        return ORDER_STATUS.COMPLETED

    if (invoice_status_set == set([INVOICE_STATUS.INVOICE_PAID]) and
            shipment_status_set != set([SHIPMENT_STATUS.DELIVER])):
        return ORDER_STATUS.AWAITING_SHIPPING

    if invoice_status_set != set([INVOICE_STATUS.INVOICE_PAID]):
        return ORDER_STATUS.AWAITING_PAYMENT

    return ORDER_STATUS.PENDING


def _update_extra_info_for_order_item(conn, item_id, order_item):
    order_item.update(
        {'shipment_info': _get_shipment_info_for_order_item(conn, item_id),
         'invoice_info': _get_invoice_info_for_order_item(conn, item_id),
         })


def get_orders_list(conn, brand_id, filter_where='', filter_params=None):
    fields, columns = zip(*(ORDER_FIELDS_COLUMNS + ORDER_ITEM_FIELDS_COLUMNS))
    query_str = '''
        SELECT %s
        FROM orders
        LEFT JOIN order_details ON order_details.id_order = orders.id
        LEFT JOIN order_items ON order_items.id = order_details.id_item
        %s
        ORDER BY confirmation_time, order_items.id
    ''' % (', '.join(columns), filter_where)
    params = filter_params or []
    results = query(conn, query_str, params=params)

    orders_dict = {}
    sorted_order_ids = []
    for result in results:
        order_item = dict(zip(fields, result))
        if not _valid_sale_brand(order_item['sale_id'], brand_id):
            continue

        order_id = order_item.pop('order_id')
        if order_id not in orders_dict:
            orders_dict[order_id] = {
                'user_info': get_user_profile(conn, order_item['user_id']),
                'user_id': order_item.pop('user_id'),
                'confirmation_time': order_item.pop('confirmation_time'),
                'first_sale_id': order_item['sale_id'],
                'order_items': []}
        item_id = order_item.pop('item_id')
        _update_extra_info_for_order_item(conn, item_id, order_item)
        orders_dict[order_id]['order_items'].append({item_id: order_item})

        if order_id not in sorted_order_ids:
            sorted_order_ids.append(order_id)

    for order_id, order in orders_dict.iteritems():
        order['order_status'] = _get_order_status(order['order_items'])

    orders = []
    for order_id in sorted_order_ids:
        orders.append({order_id: orders_dict[order_id]})
    return orders


def get_orders_filter_by_confirmation_time(conn, brand_id, start_time,
                                           end_time):
    filter_where = ('WHERE confirmation_time >= %%s AND ',
                    'confirmation_time < %%s')
    filter_params = [start_time, end_time]
    return get_orders_list(conn, brand_id, filter_where, filter_params)


def get_orders_filter_by_user(conn, brand_id, user_id):
    filter_where = 'WHERE id_user = %%s'
    filter_params = [user_id, ]
    return get_orders_list(conn, brand_id, filter_where, filter_params)


def _get_order_items(conn, order_id, brand_id):
    # {'order_items': [item_1_id: {},
    #                  item_2_id: {},
    #                  ...]
    # }
    items = {'order_items': []}
    fields, columns = zip(*ORDER_ITEM_FIELDS_COLUMNS)
    query_str = ("SELECT %s FROM order_details "
                 "LEFT JOIN order_items ON "
                 "order_details.id_item = order_items.id "
                 "WHERE id_order = %%s") % ', '.join(columns)
    results_list = query(conn, query_str, params=[order_id, ])
    for result in results_list:
        order_item = dict(zip(fields, result))
        if not _valid_sale_brand(order_item['sale_id'], brand_id):
            continue

        item_id = order_item.pop('item_id')
        _update_extra_info_for_order_item(conn, item_id, order_item)
        items['order_items'].append({item_id: order_item})
    return items


def get_order_detail(conn, order_id, brand_id):
    fields, columns = zip(*ORDER_FIELDS_COLUMNS)
    results = select(conn, 'orders', where={'id': order_id}, columns=columns)
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
    order_items = _get_order_items(conn, order_id, brand_id)
    details.update(order_items)
    details.update({
        'first_sale_id': order_items['order_items'][0].values()[0]['sale_id'],
        'order_status': _get_order_status(order_items['order_items'])})
    return details
