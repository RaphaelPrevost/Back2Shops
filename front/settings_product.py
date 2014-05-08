# frontend settings
from settings_local import *

PRODUCTION = True

USR_ROOT_URI = "http://188.165.192.57:8100"
USER_PM_FORM_URL = '%s/webservice/1.0/pub/payment/form' % USR_ROOT_URI

PP_SUCCESS = "http://188.165.192.57:9500/paypal/%(id_trans)s/success"
PP_FAILURE = "http://188.165.192.57:9500/paypal/%(id_trans)s/failure"
