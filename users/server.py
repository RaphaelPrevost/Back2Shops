import falcon
from wsgiref import simple_server

import settings
from common.db_utils import init_db_pool
from common.utils import parse_form_params
from webservice.accounts import UserResource

# falcon.API instances are callable WSGI apps
app = api = falcon.API(before=[parse_form_params])

# Resources are represented by long-lived class instances
api.add_route('/webservice/1.0/pub/account', UserResource())

init_db_pool()

if __name__ == '__main__':
    httpd = simple_server.make_server('0.0.0.0', 8100, app)
    httpd.serve_forever()
