# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


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
