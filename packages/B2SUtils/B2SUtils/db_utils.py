# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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


import psycopg2
import pypgwrap
from B2SUtils.errors import DatabaseError


global db_initialized
db_initialized = False

def init_db_pool(db_config, force=False):
    global db_initialized
    if db_initialized and not force:
        return
    db_url = ('postgres://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s'
              % db_config)
    pypgwrap.config_pool(max_pool=db_config['MAX_CONN'],
                         pool_expiration=db_config['CONN_EXPIRATION'],
                         url=db_url)
    db_initialized = True

def get_conn(db_config=None):
    global db_initialized
    if not db_initialized:
        if db_config:
            init_db_pool(db_config)
        else:
            raise DatabaseError("Database haven't! been initialized")
    return pypgwrap.connection()

def insert(conn, table_name, **kwargs):
    try:
        return conn.insert(table_name, **kwargs)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def query(conn, sql, params=None):
    try:
        return conn.query(sql, params)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def execute(conn, sql, params=None):
    try:
        return conn.execute(sql, params)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def select(conn, table_name, **kwargs):
    try:
        return conn.select(table_name, **kwargs)
    except psycopg2.Error, e:
        conn.rollback()
        raise DatabaseError("%s:%s" % (e.pgcode, e.pgerror))

def select_dict(conn, table_name, key, **kwargs):
    try:
        return conn.select_dict(table_name, key, **kwargs)
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

def join_dict(conn, tables, key, where=None, on=None, order=None,
         columns=None, limit=None, offset=None):
    try:
        return conn.join_dict(tables, key,
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
