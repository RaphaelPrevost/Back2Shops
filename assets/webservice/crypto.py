import os
import settings

class APIPubKey(object):
    def on_get(self, req, resp):
        path = settings.PUB_KEY_PATH
        resp.stream = open(path, 'rb')
        resp.stream_len = os.path.getsize(path)
        resp.content_type = 'text/plain'

