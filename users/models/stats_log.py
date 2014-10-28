import logging
from datetime import datetime

from common.redis_utils import get_redis_cli

from B2SProtocol.constants import EXPIRY_FORMAT
from B2SProtocol.constants import SESSION_COOKIE_NAME
from B2SUtils import db_utils
from B2SUtils.db_utils import insert, query, select_dict, select
from B2SUtils.common import set_cookie, get_cookie


##### visitors statistics log #####
def _up_visitors(sid, users_id):
    with db_utils.get_conn() as conn:
        db_utils.update(conn,
                        'visitors_log',
                        {'users_id': users_id},
                        where={'sid': sid})
        conn.commit()

def _log_visitors(users_id, sid):
    with db_utils.get_conn() as conn:
        values = {'sid': sid}
        if users_id:
            values['users_id'] = int(users_id)
        insert(conn, 'visitors_log', values=values)
        conn.commit()

def log_visitors(req, users_id):
    try:
        cookie = get_cookie(req)
        session = cookie and cookie.get(SESSION_COOKIE_NAME)

        if not session:
            return

        session = cookie and cookie.get(SESSION_COOKIE_NAME)
        session = session and session.value.split('&')
        session = session and [tuple(field.split('='))
                               for field in session if field]
        session = session and dict(session)
        sid = session and session['sid'] or None
        exp = (session and
               datetime.strptime(session['exp'], EXPIRY_FORMAT) or
               None)
        now = datetime.utcnow()

        cli = get_redis_cli()
        delta = int((exp - now).total_seconds())
        name = 'SID:%s' % sid

        if exp and now < exp:
            if not cli.exists(name):
                _log_visitors(users_id, sid)
            else:
                u_id = cli.get(name)
                if not u_id and users_id is not None:
                    _up_visitors(sid, users_id)
            cli.setex(name, users_id or "", delta)
        else:
            _log_visitors(users_id, sid)
            cli.setex(name, users_id or "", 0)

    except Exception, e:
        logging.error('log_visitors_err: %s', e, exc_info=True)


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

        insert(conn, 'incomes_log',
               values={'order_id': id_order,
                       'users_id': id_user,
                       'up_time': datetime.utcnow()})

    except Exception, e:
        logging.error('log_incomes_err: %s', e, exc_info=True)

def get_incomes_log(conn, where):
    incomes = select_dict(conn, 'incomes_log', 'order_id', where=where)

    where = 'WHERE '
    if not incomes:
        return []
    else:
        orders = [str(ord) for ord in incomes.keys()]
        where += 'od.id_order in (%s)' % ','.join(orders)

    q = ("SELECT od.id_order as id_order, "
                "oi.id_sale as id_sale, "
                "oi.id_shop as id_shop, "
                "oi.id_variant as id_variant, "
                "oi.price as price, "
                "od.quantity as quantity "
           "FROM order_items as oi "
           "JOIN order_details as od "
             "ON od.id_item = oi.id "
             "%s" % where)
    r = query(conn, q)

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

