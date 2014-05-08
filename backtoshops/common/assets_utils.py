import os
import logging
import ujson
import urllib2
from django.core.files.storage import Storage

import settings
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import gen_encrypt_json_context
from B2SCrypto.utils import get_from_remote
from B2SProtocol.constants import RESP_RESULT


def get_full_url(asset_name):
    return os.path.join(settings.ASSETS_CDN, asset_name)

def upload(asset_name, content):
    remote_uri = os.path.join(settings.AST_SERVER,
                              "webservice/1.0/private/upload?name=%s"
                              % urllib2.quote(asset_name))
    try:
        data = gen_encrypt_json_context(
            content.read(),
            settings.SERVER_APIKEY_URI_MAP[SERVICES.AST],
            settings.PRIVATE_KEY_PATH)

        resp = get_from_remote(
            remote_uri,
            settings.SERVER_APIKEY_URI_MAP[SERVICES.AST],
            settings.PRIVATE_KEY_PATH,
            data=data)
        return ujson.loads(resp)
    except Exception, e:
        logging.error("Failed to upload %s" % asset_name,
                      exc_info=True)
        raise


class AssetsStorage(Storage):
    def _open(self, name, mode='rb'):
        return urllib2.urlopen(self.url(name))

    def _save(self, name, content):
        result = upload(name, content)
        if result.get('res') == RESP_RESULT.F:
            raise Exception(result['err'])
        return result['location']

    def exists(self, name):
        try:
            self._open(name)
        except Exception:
            return False
        return True

    def listdir(self, path):
        pass

    def size(self, name):
        return 0

    def url(self, name):
        return get_full_url(name)

