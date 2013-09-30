from gevent import monkey
monkey.patch_all()
import gevent_psycopg2
gevent_psycopg2.monkey_patch()

import falcon
import gevent
from gevent.pywsgi import WSGIServer

import settings
from common.db_utils import init_db_pool
from common.utils import parse_form_params
from common.log import setupLogging
from urls import urlpatterns
from webservice.sales import import_sales_list

setupLogging()

# falcon.API instances are callable WSGI apps
app = api = falcon.API(before=[parse_form_params])

# Resources are represented by long-lived class instances
for url, res in urlpatterns.iteritems():
    api.add_route(url, res())

init_db_pool()
gevent.spawn(import_sales_list)

if __name__ == '__main__':
    import logging
    logging.info('user server start on port %s' % settings.SERVER_PORT)

    httpd = WSGIServer(('0.0.0.0', settings.SERVER_PORT), app)
    httpd.serve_forever()
