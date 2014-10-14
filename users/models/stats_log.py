import logging
from datetime import datetime

from common.redis_utils import get_redis_cli

from B2SProtocol.constants import EXPIRY_FORMAT
from B2SProtocol.constants import SESSION_COOKIE_NAME
from B2SUtils import db_utils
from B2SUtils.db_utils import insert, query, select_dict
from B2SUtils.common import set_cookie, get_cookie


##### visitors statistics log #####
def _up_visitors(conn, sid, users_id):
    db_utils.update(conn,
                    'visitors_log',
                    {'users_id': users_id},
                    where={'sid': sid})
    conn.commit()

def _log_visitors(conn, users_id, sid):
    values = {'sid': sid}
    if users_id:
        values['users_id'] = int(users_id)
    insert(conn, 'visitors_log', values=values)
    conn.commit()

def log_visitors(conn, req, users_id):
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
    delta = exp - now
    name = 'SID:%s' % sid

    if exp and now < exp:
        if not cli.exists(name):
            _log_visitors(conn, users_id, sid)
        else:
            u_id = cli.get(name)
            if u_id is None and users_id:
                _up_visitors(conn, sid, users_id)
    else:
        _log_visitors(conn, users_id, sid)

    cli.setex(name, users_id, delta)


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
               values={'id_order': id_order,
                       'id_user': id_user,
                       'up_time': datetime.utcnow()})

    except Exception, e:
        logging.error('log_incomes_err: %s', e, exc_info=True)
        raise

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
