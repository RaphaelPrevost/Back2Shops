# users.backtoshops.com settings
from settings_base import *

FRONT_PAYMENT_SUCCESS = "http://localhost:9500/paypal/%(id_trans)s/success"
FRONT_PAYMENT_FAILURE = "http://localhost:9500/paypal/%(id_trans)s/failure"
