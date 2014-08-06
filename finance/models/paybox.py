import datetime
from common.db_utils import update_or_create_trans


def update_or_create_trans_paybox(conn, data):
    # 'PBX_RETOUR': 'Amt:M;Ref:R;Auth:A;RespCode:E;CardType:C;PBRef:S',
    pb_trans_id = data['PBRef']
    values = {
        'id_internal_trans': data['id_trans'],
        'update_time': datetime.datetime.now(),
        'pb_trans_id': pb_trans_id,
        'amount': data['Amt'],
        'currency': data['currency'],
        'user_id': data['user_id'],
        'auth_number': data['Auth'],
        'resp_code': data['RespCode'],
    }

    return update_or_create_trans(conn, 'trans_paybox', data, values,
                                  {'pb_trans_id': pb_trans_id},
                                  data['RespCode'])
