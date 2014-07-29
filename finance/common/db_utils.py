import datetime
import logging
import ujson

from B2SUtils.db_utils import insert
from B2SUtils.db_utils import update
from B2SUtils.db_utils import execute

def update_or_create_trans(conn, table_name, data):
    values = {
        'id_internal_trans': data['id_trans'],
        'txn_id': data['txn_id'],
        'tax': data['tax'],
        'payment_status': data['payment_status'],
        'payer_id': data['payer_id'],
        'receiver_id': data['receiver_id'],
        'mc_fee': data['mc_fee'],
        'mc_currency': data['mc_currency'],
        'mc_gross': data['mc_gross'],
        'update_time': datetime.datetime.now()
    }


    try:
        id_trans = update(conn,
                          table_name,
                          where={'txn_id': data['txn_id']},
                          values=values,
                          returning='id')
        if len(id_trans) == 0:
            values['create_time'] = datetime.datetime.now()
            id_trans = insert(conn, table_name, values=values,
                              returning='id')
        else:
            id_trans = id_trans[0]

        # append new content for log
        new_content = ('; ' +
                       data['payment_status'] +
                       " : " +
                       ujson.dumps(data))

        update_sql = ("UPDATE %s "
                         "SET content = concat(content, '%s') "
                       "WHERE id = %%s"
                      % (table_name, new_content))
        execute(conn, update_sql, (id_trans[0],))
    except Exception, e:
        logging.error('create %s err: %s', table_name, e)
        raise

    return id_trans[0]

