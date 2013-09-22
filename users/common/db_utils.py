import psycopg2
import pypgwrap

import settings
from common.error import DatabaseError


global db_initialized
db_initialized = False

def init_db_pool(force=False):
    global db_initialized
    if db_initialized and not force:
        return
    db_config = settings.DATABASE
    db_url = ('postgres://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s'
              % db_config)
    pypgwrap.config_pool(max_pool=db_config['MAX_CONN'],
                         pool_expiration=db_config['CONN_EXPIRATION'],
                         url=db_url)

def get_conn():
    global db_initialized
    if not db_initialized:
        init_db_pool()
    return pypgwrap.connection()

def insert(conn, table_name, **kwargs):
    try:
        return conn.insert(table_name, **kwargs)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def query(conn, table_name, **kwargs):
    try:
        return conn.select(table_name, **kwargs)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def join(conn, tables, where=None, on=None, order=None,
         columns=None, limit=None, offset=None):
    try:
        return conn.join(tables,
                         where=where,
                         on=on,
                         order=order,
                         columns=columns,
                         limit=limit,
                         offset=offset)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def update(conn, table, values, where=None, returning=None):
    try:
        return conn.update(table, values,
                           where=where,
                           returning=returning)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def delete(conn, table, where=None, returning=None):
    try:
        return conn.delete(table,
                           where=where,
                           returning=returning)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))
