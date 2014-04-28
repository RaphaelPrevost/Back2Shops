import os

class Item(object):
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def on_get(self, req, resp, name):
        resp.content_type = self._get_media_type(name)

        image_path = os.path.join(self.storage_path, name)
        resp.stream = open(image_path, 'rb')
        resp.stream_len = os.path.getsize(image_path)

    def _get_media_type(self, ext):
        raise NotImplementedError

class JsItem(Item):
    def _get_media_type(self, ext):
        return 'application/javascript'

class CssItem(Item):
    def _get_media_type(self, ext):
        return 'text/css'

class ImgItem(Item):
    def _get_media_type(self, ext):
        ext = os.path.splitext(name)[1][1:]
        return 'image/%s' % ext

