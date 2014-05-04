import logging

from common.utils import currency_exchange
from datetime import datetime
from B2SProtocol.constants import ORDER_IV_SENT_STATUS
from B2SProtocol.constants import SHIPMENT_STATUS
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import update

from common.constants import INVOICE_STATUS

def create_invoice(conn, id_order, id_shipment, amount_due,
                   currency,
                   invoice_xml, invoice_number,
                   due_within=None,
                   amount_paid=None,
                   invoice_file=None,
                   status=INVOICE_STATUS.INVOICE_OPEN):
    values = {
        'id_order': id_order,
        'id_shipment': id_shipment,
        'creation_time': datetime.now(),
        'update_time': datetime.now(),
        'amount_due': amount_due,
        'amount_paid': amount_paid or 0,
        'currency': currency,
        'invoice_xml': invoice_xml,
        'invoice_number': invoice_number,
        'status': status
        }

    if due_within:
        values['due_within'] = due_within

    if invoice_file:
        values['invoice_file'] = invoice_file

    invoice_id = insert(conn, 'invoices', values=values, returning='id')
    logging.info('invoice created: id: %s, values: %s',
                 invoice_id[0], values)

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
    if len(id_shipments) == 1:
        where = "id_shipment = %s"
        where_condition = id_shipments[0]
    else:
        where = "id_shipment in (%s)"
        where_condition = ', '.join([str(sp) for sp in id_shipments])

    sql = """SELECT *
               FROM invoices
              WHERE %s""" % where
    r = query(conn, sql, (where_condition,))
    return r

def get_sum_amount_due(conn, id_invoices):
    if len(id_invoices) == 1:
        where = "id = %s" % id_invoices[0]
    else:
        id_invoices = [str(id_iv) for id_iv in id_invoices]
        where = "id in (%s)" % ", ".join(id_invoices)

    sql = """SELECT amount_due, currency
               FROM invoices
              WHERE %s
          """ % where
    r = query(conn, sql)

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
    if len(iv_ids) == 1:
        where = "id = %s" % iv_ids[0]
    else:
        iv_ids = [str(id_iv) for id_iv in iv_ids]
        where = "id in (%s)" % ", ".join(iv_ids)

    sql = """SELECT invoice_number
               FROM invoices
              WHERE %s
          """ % where
    r = query(conn, sql)

    return [item[0] for item in r]

def _shops_where(tb, id_shops):
    shops_where = ""
    if id_shops and len(id_shops) == 1:
        shops_where = ('AND %s.id_shop = %s'
                       % (tb, id_shops[0]))
    elif id_shops and len(id_shops) > 1:
        shops_cond = ', '.join([str(id_shop) for id_shop in id_shops])
        shops_where = ('AND %s.id_shop in (%s)'
                       % (tb, shops_cond))
    return shops_where

def _order_iv_info(conn, order_id, id_brand, id_shops):
    shops_where = _shops_where('spm', id_shops)
    sp_query = (
        "SELECT id "
          "FROM shipments as spm "
         "WHERE status <> %%s "
           "AND id_order = %%s "
           "AND id_brand = %%s "
                "%(shops_condition)s"
        % {'shops_condition': shops_where})

    sp_r = query(conn, sp_query,
                 (SHIPMENT_STATUS.DELETED, order_id, id_brand))
    sp_r = [item[0] for item in sp_r]

    # generated invoices for order.
    iv_query = (
        "SELECT id_shipment "
          "FROM invoices as iv "
     "LEFT JOIN shipments as spm "
            "ON iv.id_shipment = spm.id "
         "WHERE iv.id_order = %%s "
           "AND spm.id_brand = %%s "
                "%(shops_condition)s"
        % {"shops_condition": shops_where}
    )
    iv_r = query(conn, iv_query, (order_id, id_brand))
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

    shops_where = _shops_where('spm', id_shops)
    # sum packing quantity for order.
    pk_qty_query = (
        "SELECT sum(quantity) "
          "FROM shipping_list as spl "
          "JOIN shipments as spm "
            "ON spl.id_shipment = spm.id "
         "WHERE spm.id_order = %%s "
           "AND spm.status <> %%s "
           "AND spm.id_brand = %%s "
                "%(shops_condition)s"
        % {"shops_condition": shops_where}
    )
    pk_qty = query(conn, pk_qty_query,
                   (order_id, SHIPMENT_STATUS.DELETED, id_brand))
    pk_qty = pk_qty and pk_qty[0][0] or 0

    # sum order items quantity for order.
    shops_where = _shops_where('oi', id_shops)
    od_qty_query = (
        "SELECT sum(quantity) "
          "FROM order_details as od "
          "JOIN order_items as oi "
            "ON od.id_item = oi.id "
         "WHERE od.id_order = %%s "
                "%(shops_condition)s"
        % {"shops_condition": shops_where}
    )
    od_qty = query(conn, od_qty_query, (order_id,))[0][0]


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

    logging.info("invoice_%s updated: %s", id_iv, values)
    return r and r[0] or None