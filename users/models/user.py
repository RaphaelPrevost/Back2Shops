import ujson

from B2SUtils.db_utils import join
from B2SUtils.db_utils import select
from common.error import UserError
from common.error import ErrorCode as E_C


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

def get_user_address(conn, user_id, addr_id=None):
    user_address = {}
    columns = ['address', 'city', 'country_code', 'province_code',
               'postal_code']

    where = {'users_id': user_id}
    if addr_id:
        where['id'] = addr_id
    results = select(conn,
                     'users_address',
                     where=where,
                     columns=columns,
                     order=('id',))
    if results:
        user_address = dict(zip(columns, results[0]))

    return user_address

def get_user_dest_addr(conn, id_user, id_addr=None):
    user_address = get_user_address(conn, id_user, id_addr)
    if not user_address:
        raise UserError(E_C.UR_NO_ADDR[0],
                        E_C.UR_NO_ADDR[1] % (id_user, id_addr))
    address = {'address': user_address['address'],
               'city': user_address['city'],
               'country': user_address['country_code'],
               'province': user_address['province_code'],
               'postalcode': user_address['postal_code']}
    return ujson.dumps(address)
