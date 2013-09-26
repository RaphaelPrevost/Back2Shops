from webservice.accounts import UserResource
from webservice.auth import UserLoginResource
from webservice.aux import AuxResource
from webservice.sales import SalesResource

urlpatterns = {
    '/webservice/1.0/pub/account': UserResource,
    '/webservice/1.0/pub/connect': UserLoginResource,
    '/webservice/1.0/pub/JSONAPI': AuxResource,
    '/webservice/1.0/pub/sales/list': SalesResource,
}
