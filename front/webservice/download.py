import os
import falcon
import logging
import settings

class Item(object):
    storage_path = settings.STATIC_FILES_PATH + '/'

    def on_get(self, req, resp, name):
        path = os.path.join(self.storage_path, name)
        try:
            resp.stream = open(path, 'rb')
            resp.stream_len = os.path.getsize(path)
            resp.content_type = self._get_media_type(name)
        except IOError, e:
            logging.error("%s", e, exc_info=True)
            resp.status = falcon.HTTP_404

    def _get_media_type(self, name):
        raise NotImplementedError

class JsItem(Item):
    storage_path = settings.STATIC_FILES_PATH + '/js/'

    def _get_media_type(self, name):
        return 'application/javascript'

class CssItem(Item):
    storage_path = settings.STATIC_FILES_PATH + '/css/'

    def _get_media_type(self, name):
        return 'text/css'

class ImgItem(Item):
    storage_path = settings.STATIC_FILES_PATH + '/img/'

    def _get_media_type(self, name):
        ext = os.path.splitext(name)[1][1:]
        return 'image/%s' % ext

