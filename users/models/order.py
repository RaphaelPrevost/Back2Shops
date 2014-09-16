import logging
import ujson

from B2SProtocol.constants import ORDER_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import join
from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from B2SUtils.db_utils import update
from common.constants import INVOICE_STATUS
from models.actors.sale import CachedSale
from models.actors.shop import get_shop_id
from models.invoice import iv_to_sent_qty
from models.invoice import order_iv_sent_status
from models.shipments import get_shipments_by_order
from models.shipments import posOrderShipments
from models.shipments import wwwOrderShipments
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
        'id_shop': shop_id or 0,
        'price': sale.final_price(id_variant, id_price_type or 0),
        'name': sale.whole_name(id_variant),
        'description': sale.desc,
    }
    main_picture = sale.get_main_picture(id_variant)
    if not main_picture:
        main_picture = sale.get_main_picture()
    if main_picture:
        item_value['picture'] = main_picture
    if barcode:
        item_value['barcode'] = barcode
    if id_weight_type is not None:
        item_value['id_weight_type'] = id_weight_type
        if id_weight_type:
            item_value['type_name'] = sale.get_weight_attr(id_weight_type).name
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
    _create_order_shipment_detail(conn, order_id, shipaddr,
                                  billaddr, telephone_id)
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
                          shipaddr,
                          users_id).create()
    else:
        posOrderShipments(conn,
                          order_id,
                          order_items,
                          None,
                          users_id).create()

        # TODO: Create fake shipments for posOrder items.
        pass

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
        if not _valid_sale_brand(order_item['sale_id'], brand_id) \
                or order_item['shop_id'] not in shops_id:
            allowed = False
            break

    if allowed:
        update(conn, 'orders',
               values={'valid': False},
               where={'id': order_id})
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
                             ('id_variant', 'id_variant'),
                             ('price', 'price'),
                             ('name', 'name'),
                             ('picture', 'picture'),
                             ('description', 'description'),
                             ('copy_time', 'copy_time'),
                             ('barcode', 'barcode'),
                             ('id_weight_type', 'id_weight_type'),
                             ('id_price_type', 'id_price_type'),
                             ]


def _valid_sale_brand(sale_id, brand_id):
    if int(brand_id) == 0:
        return True

    sale = CachedSale(sale_id).sale
    return sale and sale.brand and int(sale.brand.id) == int(brand_id)

def _get_shipment_info_for_order_item(conn, item_id):
    fields, columns = zip(*[('shipment_id', 'shipments.id'),
                            ('status', 'shipments.status'),
                            ('handling_fee', 'handling_fee'),
                            ('shipping_fee', 'shipping_fee'),
                            ('shipping_date', 'shipping_date'),
                            ('shipping_list_quantity', 'quantity'),
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

def _get_order_shipments_status(conn, id_order):
    query_str = ("SELECT status "
                   "FROM shipments "
                  "WHERE id_order = %s")
    rst = query(conn, query_str, (id_order,))
    return [item[0] for item in rst]

def _get_order_invoice_status(conn, id_order):
    query_str = ("SELECT status "
                   "FROM invoices "
                  "WHERE id_order = %s")
    rst = query(conn, query_str, (id_order,))
    return [item[0] for item in rst]

def _all_order_items_packed(conn, id_order):
    item_qtt_sql = ("SELECT sum(quantity) "
                      "FROM order_details "
                     "WHERE id_order = %s")

    grouped_qtt_sql = ("SELECT sum(spl.quantity), sum(spl.packing_quantity) "
                         "FROM shipping_list as spl "
                         "JOIN shipments as sp "
                           "ON spl.id_shipment = sp.id "
                        "WHERE sp.id_order = %s "
                          "AND sp.status <> %s")
    item_qtt = query(conn, item_qtt_sql, (id_order,))[0][0]
    grouped_qtt, packed_qtt = query(conn,
                        grouped_qtt_sql,
                        (id_order, SHIPMENT_STATUS.DELETED))[0]

    return item_qtt == grouped_qtt and item_qtt == packed_qtt

def get_order_status(conn, order_id):
    """
    There is 4 status.
    Pending order is the initial status.
    When all the the shipments are created and matching invoices as well, the
    order becomes "awaiting payment".
    When all the invoices are paid, the order becomes "awaiting shipping".
    When the merchant has set the status of all shipments as sent, the order
    is "completed".
    """
    shipment_status_set = set(_get_order_shipments_status(conn, order_id))
    invoice_status_set = set(_get_order_invoice_status(conn, order_id))

    if shipment_status_set == set([SHIPMENT_STATUS.FETCHED]):
        return ORDER_STATUS.COMPLETED

    if (invoice_status_set == set([INVOICE_STATUS.INVOICE_PAID]) and
            shipment_status_set == set([SHIPMENT_STATUS.DELIVER])):
        return ORDER_STATUS.COMPLETED

    if (invoice_status_set == set([INVOICE_STATUS.INVOICE_PAID]) and
            shipment_status_set != set([SHIPMENT_STATUS.DELIVER])):
        return ORDER_STATUS.AWAITING_SHIPPING

    if (invoice_status_set != set([INVOICE_STATUS.INVOICE_PAID]) and
        _all_order_items_packed(conn, order_id)):
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

def get_orders_list(conn, brand_id, shops_id,
                    users_id=None, limit=None, offset=None):
    fields, columns = zip(*(ORDER_FIELDS_COLUMNS +
                            ORDER_SHIPMENT_COLUMNS +
                            ORDER_ITEM_FIELDS_COLUMNS))

    filter_where = "where orders.valid "
    params = []
    if users_id:
        filter_where += " and orders.id_user=%s"
        params.append(users_id)
    elif shops_id:
        filter_where += (" and order_items.id_shop in (%s)"
                 % ', '.join(['%s'] * len(shops_id)))
        params += shops_id

    order_by = "ORDER BY confirmation_time, order_items.id"
    if users_id:
        order_by = "ORDER BY confirmation_time desc, orders.id desc"

    limit_offset = ""
    if limit:
        limit_offset += " limit %s "
        params.append(limit)
    if offset:
        limit_offset += " offset %s"
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
        if not _valid_sale_brand(order_item['sale_id'], brand_id):
            continue

        order_id = order_item.pop('order_id')
        if order_id not in orders_dict:
            id_user = order_item.pop('user_id')
            id_shipaddr = order_item.pop('id_shipaddr')
            id_phone = order_item.pop('id_phone')
            orders_dict[order_id] = {
                'user_info': get_user_profile(conn, id_user),
                'user_id': id_user,
                'confirmation_time': order_item.pop('confirmation_time'),
                'first_sale_id': order_item['sale_id'],
                'shipping_dest': get_user_dest_addr(conn, id_user, id_shipaddr),
                'contact_phone': get_user_sel_phone_num(conn, id_user, id_phone),
                'order_items': [],
                'shop_ids': []}
        item_id = order_item.pop('item_id')
        _update_extra_info_for_order_item(conn, item_id, order_item)
        orders_dict[order_id]['order_items'].append({item_id: order_item})
        orders_dict[order_id]['shop_ids'].append(order_item['shop_id'])

        if order_id not in sorted_order_ids:
            sorted_order_ids.append(order_id)

    for order_id, order in orders_dict.iteritems():
        order['order_status'] = get_order_status(conn, order_id)
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

        if not _valid_sale_brand(order_item['sale_id'], brand_id):
            continue

        item_id = order_item.pop('item_id')
        _update_extra_info_for_order_item(conn, item_id, order_item)
        items['order_items'].append({item_id: order_item})
    return items

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
        'first_sale_id': order_items['order_items'][0].values()[0]['sale_id'],
        'shipping_dest': get_user_dest_addr(conn, details['user_id'],
                                            details['id_shipaddr']),
        'order_status': get_order_status(conn, order_id)})
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
