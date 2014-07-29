from common.db_utils import update_or_create_trans


def update_or_create_trans_paypal(conn, data):
    return update_or_create_trans(conn, 'trans_paypal', data)
