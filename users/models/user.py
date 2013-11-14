from B2SUtils.db_utils import join
from B2SUtils.db_utils import select


def get_user_address(conn, user_id):
    # {'address': {add_1_id: {...},
    #              add_2_id: {...}
    #              ...}
    # }
    user_address_dict = {'address': {}}

    columns = ['users_address.id', 'addr_type', 'address', 'city',
               'postal_code', 'country_code', 'province_code', 'address_desp']
    results = join(conn, ['users, users_address'],
                   where={'users.id': user_id, 'valid': True},
                   columns=columns)

    for result in results:
        u_addr_id = result[0]
        addr_dict = dict(zip(columns[1:], result[1:]))
        user_address_dict['address'].update({u_addr_id: addr_dict})
    return user_address_dict


def get_user_phone_num(conn, user_id):
    # {'phone_num': {phone_1_id: {...},
    #                phone_2_id: {...}
    #                ...}
    # }
    user_phone_num_dict = {'phone_num': {}}
    columns = ['users_phone_num.id', 'country_num', 'phone_num',
               'phone_num_desp']
    results = join(conn, ['users, users_phone_num'],
                   where={'users.id': user_id, 'valid': True},
                   columns=columns)
    for result in results:
        u_phone_id = result[0]
        phone_dict = dict(zip(columns[1:], result[1:]))
        user_phone_num_dict['phone_num'].update({u_phone_id: phone_dict})
    return user_phone_num_dict


def get_user_profile(conn, user_id):
    user_profile = {}
    columns = ['locale', 'title', 'first_name', 'last_name', 'gender',
               'birthday']
    results = select(conn, 'users_profile', where={'users_id': user_id},
                     columns=columns)
    if results:
        user_profile = dict(zip(columns, results[0]))
    return user_profile
