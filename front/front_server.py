from gevent import monkey
monkey.patch_all()

import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from common.data_access import data_access
import static
from urls import urlpatterns
from B2SUtils.log import setupLogging
from B2SFrontUtils.constants import REMOTE_API_NAME
from B2SFrontUtils.utils import parse_form_params


setupLogging(settings.LOG_CONFIG_FILE)

# falcon.API instances are callable WSGI apps
app = api = falcon.API(before=[parse_form_params])

# Resources are represented by long-lived class instances
for url, res in urlpatterns.iteritems():
    api.add_route(url, res())
# serve static files
static_path = settings.STATIC_FILES_PATH
api.add_route('/js/{name}', static.JsItem(static_path + '/js/'))
api.add_route('/css/{name}', static.CssItem(static_path + '/css/'))
api.add_route('/img/{name}', static.ImgItem(static_path + '/img/'))


def load_data():
    data_access(REMOTE_API_NAME.GET_SALES)

if __name__ == '__main__':
    gevent.spawn(load_data)

    import logging
    logging.info('frontend instance start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "frontend instance is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()
