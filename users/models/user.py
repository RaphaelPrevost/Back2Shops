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


def get_user_phone_num(conn, user_id, id_phone=None):
    """
    @param conn: database connection
    @param user_id: user's id.
    @param id_phone: id of users_phone_num
    @return: [{'id': ...,
               'country_num': ...,
               'phone_num': ...,
               'phone_num_desc': ...},
               ...]
    """
    where = {'users_id': user_id}
    if id_phone:
        where['id'] = id_phone
    columns = ['id', 'country_num', 'phone_num',
               'phone_num_desp']
    results = select(conn,
                    'users_phone_num',
                    where=where,
                   columns=columns)
    return [dict(zip(columns, result)) for result in results]

def get_user_sel_phone_num(conn, id_user, id_phone=None):
    phones = get_user_phone_num(conn, id_user, id_phone)
    if not phones:
        raise UserError(E_C.UR_NO_PHONE[0],
                        E_C.UR_NO_PHONE[1] % (id_user, id_phone))
    return phones[0]


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
    """
    @param conn: database connection
    @param user_id: user's id.
    @param addr_id: id of users_address
    @return: [{'id': ...,
               'address': ...,
               'city': ...,
               'country_code': ...,
               'province_code': ...,
               'postal_code': ...},
               ...]
    """
    columns = ['id', 'address', 'city', 'country_code', 'province_code',
               'postal_code']

    where = {'users_id': user_id}
    if addr_id:
        where['id'] = addr_id
    results = select(conn,
                     'users_address',
                     where=where,
                     columns=columns,
                     order=('id',))

    return [dict(zip(columns, result)) for result in results]

def get_user_dest_addr(conn, id_user, id_addr=None):
    """
    @param conn: database connection
    @param user_id: user's id.
    @param addr_id: id of users_address
    @return: {'address': ...,
              'city': ...,
              'country': ...,
              'province': ...,
              'postalcode': ...}
    """
    user_address = get_user_address(conn, id_user, id_addr)
    if not user_address:
        raise UserError(E_C.UR_NO_ADDR[0],
                        E_C.UR_NO_ADDR[1] % (id_user, id_addr))
    user_address = user_address[0]
    address = {'address': user_address['address'],
               'city': user_address['city'],
               'country': user_address['country_code'],
               'province': user_address['province_code'],
               'postalcode': user_address['postal_code']}
    return address

def get_user_email(conn, id_user):
    where = {'id': id_user}
    r = select(conn, 'users', where=where, columns=['email'])
    return r and r[0][0] or None
