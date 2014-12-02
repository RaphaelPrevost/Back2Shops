from B2SUtils.db_utils import query
from B2SUtils.db_utils import select
from common.error import UserError
from common.error import ErrorCode as E_C


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
               'birthday', 'users_id']
    results = select(conn, 'users_profile', where={'users_id': user_id},
                     columns=columns)
    if results:
        user_profile = dict(zip(columns, results[0]))

    user_profile.update({'email': get_user_email(conn, user_id)})
    return user_profile


ADDR_FIELDS_COLUMNS = [
    ('id', 'users_address.id'),
    ('address', 'users_address.address'),
    ('address2','users_address.address2'),
    ('city','users_address.city'),
    ('country','users_address.country_code'),
    ('province','users_address.province_code'),
    ('postalcode','users_address.postal_code'),
    ('full_name', 'users_address.full_name'),
    ('calling_code', 'country_calling_code.calling_code'),

]
def get_user_address(conn, user_id, addr_id=None):
    """
    @param conn: database connection
    @param user_id: user's id.
    @param addr_id: id of users_address
    @return: [{'id': ...,
               'address': ...,
               'address2': ...,
               'city': ...,
               'country_code': ...,
               'province_code': ...,
               'postal_code': ...,
               'full_name': ...},
               ...]
    """
    fields, columns = zip(*ADDR_FIELDS_COLUMNS)

    where = "WHERE users_id = %s "
    params = [user_id]
    if addr_id:
        where += "AND id = %s "
        params.append(addr_id)

    query_str = (
        "SELECT %s "
          "FROM users_address "
          "LEFT JOIN country_calling_code "
            "ON users_address.country_code = country_calling_code.country_code "
            "%s"
      "ORDER BY users_address.id"
    ) % (", ".join(columns), where)

    results = query(conn, query_str, params=params)

    customer_name = None
    addrs = [dict(zip(fields, result)) for result in results]
    for addr in addrs:
        if not addr['full_name']:
            if not customer_name:
                profile = get_user_profile(conn, user_id)
                customer_name = ' '.join([profile['first_name'],
                                          profile['last_name']])
            addr['full_name'] = customer_name
    return addrs

def get_user_dest_addr(conn, id_user, id_addr=None):
    """
    @param conn: database connection
    @param user_id: user's id.
    @param addr_id: id of users_address
    @return: {'address': ...,
              'address2': ...,
              'city': ...,
              'country': ...,
              'province': ...,
              'postalcode': ...}
    """
    user_address = get_user_address(conn, id_user, id_addr)
    if not user_address:
        raise UserError(E_C.UR_NO_ADDR[0],
                        E_C.UR_NO_ADDR[1] % (id_user, id_addr))
    return user_address[0]

def get_user_email(conn, id_user):
    where = {'id': id_user}
    r = select(conn, 'users', where=where, columns=['email'])
    return r and r[0][0] or None
