# frontend settings
from settings_local import *

PRODUCTION = True

USR_ROOT_URI = "http://92.222.30.2"
USER_PM_FORM_URL = '%s/webservice/1.0/pub/payment/form' % USR_ROOT_URI

FRONT_ROOT_URI = "http://92.222.30.5"
PP_SUCCESS = "%s/paypal/%%(id_trans)s/success" % FRONT_ROOT_URI
PP_FAILURE = "%s/paypal/%%(id_trans)s/failure" % FRONT_ROOT_URI

BRAND_ID = "1000001" #TODO
