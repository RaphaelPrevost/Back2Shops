import logging
import os
from datetime import datetime

import settings
from B2SUtils import db_utils


def main():
    size = settings.HMAC_KEY_SIZE
    path = settings.HMAC_KEY_FILE_PATH
    hmac_key = os.urandom(size)

    with open(path, 'w') as f:
        f.write(hmac_key)
        f.close()
        logging.info('HMAC key updated at %s UTC: %s'
                     % (datetime.utcnow(), hmac_key))

    with db_utils.get_conn(settings.DATABASE) as conn:
        result = db_utils.delete(conn, 'users_logins',
                        where={'cookie_expiry__lt': datetime.utcnow()},
                        returning='*')
        if result:
            logging.info('Delete expiry login sessions at %s UTC: %s'
                         % (datetime.utcnow(), result))
        else:
            logging.info('No sessions expired')


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        logging.error('HMAC key update Error: %s' % e, exc_info=True)
