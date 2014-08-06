import datetime
import logging
import ujson

from B2SUtils.db_utils import insert
from B2SUtils.db_utils import update
from B2SUtils.db_utils import execute

def update_or_create_trans(conn, table_name, data, values, where, status):
    try:
        id_trans = update(conn,
                          table_name,
                          where=where,
                          values=values,
                          returning='id')
        if len(id_trans) == 0:
            values['create_time'] = datetime.datetime.now()
            id_trans = insert(conn, table_name, values=values,
                              returning='id')
        else:
            id_trans = id_trans[0]

        # append new content for log
        new_content = ('; ' +
                       status +
                       " : " +
                       ujson.dumps(data))

        update_sql = ("UPDATE %s "
                         "SET content = concat(content, '%s') "
                       "WHERE id = %%s"
                      % (table_name, new_content))
        execute(conn, update_sql, (id_trans[0],))
    except Exception, e:
        logging.error('create %s err: %s', table_name, e)
        raise

    return id_trans[0]
