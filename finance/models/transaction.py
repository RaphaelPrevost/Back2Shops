# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
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


import logging
import ujson

from datetime import datetime
from B2SUtils.db_utils import insert
from B2SUtils.db_utils import query
from B2SUtils.db_utils import update
from B2SUtils.db_utils import select
from B2SProtocol.constants import TRANS_STATUS

def create_trans(conn, id_order, id_user, id_invoices,
                 iv_numbers, amount_due, currency, invoices_data,
                 status=TRANS_STATUS.TRANS_OPEN,
                 create_time=None,
                 update_time=None,
                 cookie=None):
    if isinstance(id_invoices, list):
        id_invoices = ujson.dumps(id_invoices)

    # if there is an existing open transaction for this order and invoices,
    # return it directly to avoid creating duplicate transactions
    check = select(conn, 'transactions',  columns=("id","cookie",), where={
        'id_order': id_order,
        'id_invoices': id_invoices,
        'status': TRANS_STATUS.TRANS_OPEN,
    })
    if len(check) > 0:
        return row[0][0]
    
    if (create_time == None):
        create_time = datetime.now()
    if (update_time == None):
        update_time = datetime.now()
    
    values = {
        'id_order': id_order,
        'id_user': id_user,
        'id_invoices': id_invoices,
        'iv_numbers': iv_numbers,
        'status': status,
        'create_time': create_time,
        'update_time': update_time,
        'amount_due': amount_due,
        'currency': currency,
        'invoices_data': invoices_data
        }

    if cookie is not None:
        values['cookie'] = cookie

    trans_id = insert(conn, 'transactions', values=values, returning='id')
    logging.info('transaction created: id: %s, values: %s',
                 trans_id[0], values)

    return trans_id[0]


def update_trans(conn, values, where=None):
    values.update({'update_time': datetime.now()})
    r = update(conn,
               "transactions",
               values=values,
               where=where,
               returning="id")
    logging.info('transaction_update, values - %s, where - %s',
                 values,
                 where)
    return r

def get_trans_by_id(conn, id_trans):
    sql = ("SELECT * "
           "FROM transactions "
           "WHERE id=%s")
    r = query(conn, sql, (id_trans,))
    return r