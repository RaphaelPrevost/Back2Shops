import logging

from datetime import datetime
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query

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

def get_sum_amount_due(conn, id_invoices):
    if len(id_invoices) == 1:
        where = "id = %s" % id_invoices[0]
    else:
        where = "id in (%s)" % ", ".join(id_invoices)

    sql = """SELECT sum(amount_due)
               FROM invoices
               WHERE %s
          """ % where
    r = query(conn, sql)
    return r and r[0][0] or None