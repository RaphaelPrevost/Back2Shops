# users.backtoshops.com settings

from common.constants import HASH_ALGORITHM

DATABASE = {
    'NAME': 'users',
    'USER': 'postgres',
    'PASSWORD': '',
    'HOST': 'localhost',
    'PORT': '5432',
    'MAX_CONN': 10,
    'CONN_EXPIRATION': 1, #minute
}

DEFAULT_PASSWORD_HASH_ALGORITHM = HASH_ALGORITHM.WHIRLPOOL
HASH_MIN_ITERATIONS = 2
HASH_MAX_ITERATIONS = 256
USER_CREATION_CAPTCHA = "1234" # temporary solution for now
