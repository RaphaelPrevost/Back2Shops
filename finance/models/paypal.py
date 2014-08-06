import datetime
from common.db_utils import update_or_create_trans


def update_or_create_trans_paypal(conn, data):
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

    return update_or_create_trans(conn, 'trans_paypal', data, values,
                                  {'txn_id': data['txn_id']},
                                  data['payment_status'])
