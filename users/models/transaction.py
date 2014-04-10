import logging
import ujson

from datetime import datetime
from B2SUtils.db_utils import insert
from B2SProtocol.constants import TRANS_STATUS

def create_trans(conn, id_order, id_invoices,
                 amount_due, cookie,
                 status=TRANS_STATUS.TRANS_OPEN,
                 create_time=datetime.now(),
                 update_time=datetime.now()):
    if isinstance(id_invoices, list):
        id_invoices = ujson.dumps(id_invoices)
    values = {
        'id_order': id_order,
        'id_invoices': id_invoices,
        'status': status,
        'create_time': create_time,
        'update_time': update_time,
        'amount_due': amount_due,
        'cookie': cookie
        }

    trans_id = insert(conn, 'transactions', values=values, returning='id')
    logging.info('transaction created: id: %s, values: %s',
                 trans_id[0], values)

    return trans_id[0]
