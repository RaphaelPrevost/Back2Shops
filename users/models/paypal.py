import logging
import ujson

from B2SUtils.db_utils import insert

def create_trans_paypal(conn, data):
    values = {
        'id_interval_trans': data['id_trans'],
        'txn_id': data['txn_id'],
        'tax': data['tax'],
        'payment_status': data['payment_status'],
        'payer_id': data['payer_id'],
        'receiver_id': data['receiver_id'],
        'mc_fee': data['mc_fee'],
        'mc_currency': data['mc_currency'],
        'mc_gross': data['mc_gross'],
        'content': ujson.dumps(data)
    }

    try:
        id_trans = insert(conn, 'trans_paypal', values=values,
                          returning='id')
    except Exception, e:
        logging.error('create_trans_paypal_err: %s', e)
        raise

    return id_trans[0]

