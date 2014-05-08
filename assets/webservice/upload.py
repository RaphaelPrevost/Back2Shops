import os
import falcon
import ujson

import settings
from webservice.base import BaseJsonResource
from B2SCrypto.constant import SERVICES
from B2SCrypto.utils import decrypt_json_resp
from B2SCrypto.utils import gen_encrypt_json_context
from B2SProtocol.constants import RESP_RESULT
from B2SUtils.errors import ValidationError


class Collection(BaseJsonResource):

    def _on_post(self, req, resp, **kwargs):
        filename = req.get_param('name', required=True)
        storage_path = os.path.join(settings.STATIC_FILES_PATH, filename)

        directory = os.path.dirname(storage_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        content = decrypt_json_resp(req.stream,
                                 settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                                 settings.PRIVATE_KEY_PATH)
        with open(storage_path, 'wb') as _f:
            _f.write(content)

        resp.status = falcon.HTTP_201
        return {'res': RESP_RESULT.S,
                'location': filename}

    def gen_resp(self, resp, data_dict):
        resp.content_type = "application/json"
        resp.body = gen_encrypt_json_context(
                            ujson.dumps(data_dict),
                            settings.SERVER_APIKEY_URI_MAP[SERVICES.ADM],
                            settings.PRIVATE_KEY_PATH)
        return resp

