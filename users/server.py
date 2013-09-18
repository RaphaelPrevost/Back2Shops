import falcon
from wsgiref import simple_server

import settings
from urls import urlpatterns
from common.db_utils import init_db_pool
from common.utils import parse_form_params
from common.log import setupLogging

setupLogging()

# falcon.API instances are callable WSGI apps
app = api = falcon.API(before=[parse_form_params])

# Resources are represented by long-lived class instances
for url, res in urlpatterns.iteritems():
    api.add_route(url, res())

init_db_pool()

if __name__ == '__main__':
    import logging
    logging.info('user server start on port 8100')
    httpd = simple_server.make_server('0.0.0.0', 8100, app)
    httpd.serve_forever()
