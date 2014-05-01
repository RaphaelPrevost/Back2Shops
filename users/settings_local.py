# users.backtoshops.com settings
from settings_base import *

FRONT_PAYMENT_SUCCESS = "http://jessica-pc:9500/payment/%(id_trans)s/success"
FRONT_PAYMENT_FAILURE = "http://jessica-pc:9500/payment/%(id_trans)s/failure"
