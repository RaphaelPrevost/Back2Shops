import os
import settings
import logging

from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote

def remote_payment_init(data):
    uri = "webservice/1.0/private/payment/init"
    remote_uri = os.path.join(settings.FIN_SERVER, uri)
    try:
        data = gen_encrypt_json_context(
            data,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.FIN],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            remote_uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.FIN],
            settings.PRIVATE_KEY_PATH,
            data=data,
            headers={'Content-Type': 'application/json'})
        return resp
    except Exception, e:
        logging.error("Failed to send shipping fee %s" % data,
                      exc_info=True)
        raise
