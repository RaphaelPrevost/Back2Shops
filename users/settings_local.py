# users.backtoshops.com settings
from settings_base import *

DEFAULT_REDIS_CACHE_TTL = 1 * 60

FRONT_PAYMENT_SUCCESS = "http://localhost:9500/paypal/%(id_trans)s/success"
FRONT_PAYMENT_FAILURE = "http://localhost:9500/paypal/%(id_trans)s/failure"
