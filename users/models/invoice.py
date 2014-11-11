import logging

from common.utils import currency_exchange
from datetime import datetime
from B2SProtocol.constants import INVOICE_STATUS
from B2SProtocol.constants import ORDER_IV_SENT_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SUtils.common import to_round
from B2SUtils.db_utils import delete
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from B2SUtils.db_utils import select_dict
from B2SUtils.db_utils import update

def create_invoice(conn, id_order, id_shipment, amount_due,
                   currency,
                   invoice_xml, invoice_number,
                   due_within=None,
                   shipping_within=None,
                   amount_paid=None,
                   invoice_file=None,
                   invoice_items=None,
                   status=INVOICE_STATUS.INVOICE_OPEN):
    values = {
        'id_order': id_order,
        'id_shipment': id_shipment,
        'creation_time': datetime.now(),
        'update_time': datetime.now(),
        'amount_due': to_round(amount_due),
        'amount_paid': to_round(amount_paid or 0),
        'currency': currency,
        'invoice_xml': invoice_xml,
        'invoice_number': invoice_number,
        'status': status
        }

    if due_within:
        values['due_within'] = due_within
    if shipping_within:
        values['shipping_within'] = shipping_within
    if invoice_items:
        values['invoice_items'] = invoice_items

    if invoice_file:
        values['invoice_file'] = invoice_file

    invoice_id = insert(conn, 'invoices', values=values, returning='id')
    logging.info('invoice created: id: %s, values: %s',
                 invoice_id[0], values)

    seller = get_seller(conn, id_shipment)

    from models.order import up_order_log
    up_order_log(conn, id_order, seller)
    return invoice_id[0]

def get_invoice_by_order(conn, id_order):
    sql = """SELECT *
               FROM invoices
              WHERE id_order = %s"""
    r = query(conn, sql, (id_order,))
    return r

def get_invoice_by_id(conn, id_iv):
    query_str = ("SELECT * "
                   "FROM invoices "
                  "WHERE id = %s")
    r = query(conn, query_str, (id_iv,))
    return r and r[0] or None

def get_invoices_by_shipments(conn, id_shipments):
    assert len(id_shipments) > 0

    sql = """SELECT *
               FROM invoices
              WHERE id_shipment in %s"""
    r = query(conn, sql, [tuple(id_shipments)])
    return r

def get_sum_amount_due(conn, id_invoices):
    sql = """SELECT amount_due, currency
               FROM invoices
              WHERE id in %s
          """
    r = query(conn, sql, [tuple(id_invoices)])

    currency = set([item[1] for item in r])
    sum_amount = 0.0
    if len(currency) > 1:
        for amount_due, from_currency in r:
            due = currency_exchange(from_currency, 'EUR', amount_due)
            sum_amount += due
        return sum_amount, 'EUR'
    elif len(currency) == 1:
        for amount_due, _ in r:
            sum_amount += amount_due
        return sum_amount, list(currency)[0]

    return None, None

def get_iv_numbers(conn, iv_ids):
    sql = """SELECT invoice_number
               FROM invoices
              WHERE id in %s
          """
    r = query(conn, sql, [tuple(iv_ids)])

    return [item[0] for item in r]

def _order_iv_info(conn, order_id, id_brand, id_shops):
    sp_query = (
        "SELECT id "
          "FROM shipments as spm "
         "WHERE status <> %s "
           "AND id_order = %s "
           "AND id_brand = %s "
           )

    params = [SHIPMENT_STATUS.DELETED, order_id, id_brand]
    if id_shops:
        sp_query += "AND spm.id_shop in %s "
        params.append(tuple(id_shops))

    sp_r = query(conn, sp_query, params)
    sp_r = [item[0] for item in sp_r]

    # generated invoices for order.
    iv_query = (
        "SELECT id_shipment "
          "FROM invoices as iv "
     "LEFT JOIN shipments as spm "
            "ON iv.id_shipment = spm.id "
         "WHERE iv.id_order = %s "
           "AND spm.id_brand = %s ")

    params = [order_id, id_brand]
    if id_shops:
        iv_query += "AND spm.id_shop in %s "
        params.append(tuple(id_shops))
    iv_r = query(conn, iv_query, params)
    iv_r = [item[0] for item in iv_r]
    return sp_r, iv_r

def iv_to_sent_qty(conn, order_id, id_brand, id_shops):
    sp_r, iv_r = _order_iv_info(conn, order_id, id_brand, id_shops)
    return len(set(sp_r) - set(iv_r))

def order_iv_sent_status(conn, order_id, id_brand, id_shops):
    sp_r, iv_r = _order_iv_info(conn, order_id, id_brand, id_shops)

    if len(sp_r) > 0 and len(iv_r) == 0:
        return ORDER_IV_SENT_STATUS.NO_SENT
    elif len(set(sp_r) - set(iv_r)) > 0:
        return ORDER_IV_SENT_STATUS.PART_SENT

    # sum packing quantity for order.
    pk_qty_query = (
        "SELECT sum(quantity) "
          "FROM shipping_list as spl "
          "JOIN shipments as spm "
            "ON spl.id_shipment = spm.id "
         "WHERE spm.id_order = %s "
           "AND spm.status <> %s "
           "AND spm.id_brand = %s "
    )

    params = [order_id, SHIPMENT_STATUS.DELETED, id_brand]
    if id_shops:
        pk_qty_query += "AND spm.id_shop in %s "
        params.append(tuple(id_shops))

    pk_qty = query(conn, pk_qty_query, params)
    pk_qty = pk_qty and pk_qty[0][0] or 0

    # sum order items quantity for order.
    od_qty_query = (
        "SELECT sum(quantity) "
          "FROM order_details as od "
          "JOIN order_items as oi "
            "ON od.id_item = oi.id "
         "WHERE od.id_order = %s "

    )
    params = [order_id]
    if id_shops:
        od_qty_query += "AND oi.id_shop in %s"
        params.append(tuple(id_shops))

    od_qty = query(conn, od_qty_query, params)[0][0]


    if od_qty - pk_qty > 0:
        return ORDER_IV_SENT_STATUS.WAITING_SPM_CREATE
    else:
        return ORDER_IV_SENT_STATUS.SENT

def update_invoice(conn, id_iv, values, iv=None):
    where = {'id': id_iv}

    values['update_time'] = datetime.now()
    if iv is None or iv['id'] != int(id_iv):
        iv = get_invoice_by_id(conn, id_iv)
    if iv is None:
        logging.error('iv_update_err: invoice %s not exist',
                      id_iv)
        return

    r = update(conn,
               "invoices",
               values=values,
               where=where,
               returning='id')
    if (values.get('status') and
        int(values.get('status') != iv['status'])):
        insert(conn,
               'invoice_status',
               values={'id_invoice': id_iv,
                       'status': iv['status'],
                       'amount_paid': iv['amount_paid'],
                       'timestamp': iv['update_time']})

        seller = get_seller(conn, iv['id_shipment'])
        from models.order import up_order_log
        up_order_log(conn, iv['id_order'], seller)

    logging.info("invoice_%s updated: %s", id_iv, values)
    return r and r[0] or None

def delete_invoices(conn, where):
    invoices = select_dict(conn, 'invoices', 'id', where=where)
    deleted_invoice_ids = []
    for id, invoice in invoices.iteritems():
        delete(conn, 'invoice_status', where={'id_invoice': id})
        invoice_id = delete(conn, 'invoices', where={'id': id}, returning='id')
        deleted_invoice_ids.append(invoice_id)
        logging.info('invoice %s deleted for %s', invoice_id, where)
    return deleted_invoice_ids

def get_seller(conn, id_shipment):
    r = select(conn, 'shipments', where={'id': id_shipment})
    return {r[0]['id_brand']: [r[0]['id_shop']]}
