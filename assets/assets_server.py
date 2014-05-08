from gevent import monkey
monkey.patch_all()

import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from urls import urlpatterns
from B2SUtils.log import setupLogging

setupLogging(settings.LOG_CONFIG_FILE)

# falcon.API instances are callable WSGI apps
app = api = falcon.API()

# Resources are represented by long-lived class instances
for url, res in urlpatterns.iteritems():
    api.add_route(url, res())

if __name__ == '__main__':
    import logging
    logging.info('assets instance start on port %s' % settings.SERVER_PORT)

    listener = ('0.0.0.0', settings.SERVER_PORT)
    print "assets instance is running at http://%s:%s" % listener
    httpd = WSGIServer(listener, app)
    httpd.serve_forever()
