from B2SUtils.db_utils import query


PROCESSOR_FIELDS = ['id', 'name', 'img']
def get_processor(conn):
    sql = "SELECT %s from processor" % ', '.join(PROCESSOR_FIELDS)
    r = query(conn, sql)
    proc_list = []
    for item in r:
        proc_list.append(dict(zip(PROCESSOR_FIELDS, item)))
    return proc_list