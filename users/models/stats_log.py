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
from datetime import datetime

from B2SUtils import db_utils
from B2SUtils.db_utils import insert, query, select_dict, select


##### incomes statistics #####
def log_incomes(conn, iv_id):
    try:
        q = ("SELECT id_order "
               "FROM invoices "
              "WHERE id = %s")
        r = query(conn, q, (iv_id,))
        id_order = r[0][0]

        q = ("SELECT id_user "
             "FROM orders "
             "WHERE id = %s")
        r = query(conn, q, (id_order,))
        id_user = r[0][0]

        results = select(conn, 'incomes_log', where={'order_id': id_order})
        if len(results) == 0:
            insert(conn, 'incomes_log',
                   values={'order_id': id_order,
                           'users_id': id_user,
                           'up_time': datetime.utcnow()})

    except Exception, e:
        logging.error('log_incomes_err: %s', e, exc_info=True)

def get_incomes_log(conn, where):
    incomes = select_dict(conn, 'incomes_log', 'order_id', where=where)

    if not incomes:
        return []

    q = ("SELECT od.id_order as id_order, "
                "oi.id_sale as id_sale, "
                "oi.id_shop as id_shop, "
                "oi.id_variant as id_variant, "
                "oi.price as price, "
                "od.quantity as quantity "
           "FROM order_items as oi "
           "JOIN order_details as od "
             "ON od.id_item = oi.id "
          "WHERE od.id_order in %s")
    r = query(conn, q, [tuple(incomes.keys())])

    details = [dict(income) for income in r]
    for detail in details:
        id_order = detail['id_order']
        detail.update({'up_time': incomes[id_order]['up_time'],
                       'id_user': incomes[id_order]['users_id']})
    return details

##### orders statistics #####
def get_orders_log(conn, from_, to):
    try:
        q = ("SELECT * "
               "FROM orders_log "
              "WHERE (pending_date >= %s AND pending_date < %s) or "
                    "(waiting_payment_date >= %s AND waiting_payment_date < %s) or "
                    "(waiting_shipping_date >= %s AND waiting_shipping_date < %s) or "
                    "(completed_date >=%s AND completed_date < %s)")
        r = query(conn, q, (from_, to, from_, to, from_, to, from_, to))
        return r
    except Exception, e:
        logging.error('get_orders_log: %s', e, exc_info=True)


##### customers who bought also bought history #####
def gen_bought_history(users_id, id_sales):
    try:
        with db_utils.get_conn() as conn:
            for id_sale in id_sales:
                insert(conn,
                       'bought_history',
                       values={'id_sale': id_sale,
                               'users_id': users_id})
            conn.commit()
    except Exception, e:
        logging.error('gen_bought_history_err: %s', e)

def get_bought_history(conn):
    return select(conn, 'bought_history')

