from webservice.accounts import UserResource
from webservice.auth import UserLoginResource
from webservice.aux import AuxResource
from webservice.cache_invalidation import InvalidationResource
from webservice.shops import ShopsResource
from webservice.crypto import ApiKeyResource
from webservice.crypto import CryptoTestResource
from webservice.sales import SalesResource

urlpatterns = {
    '/webservice/1.0/pub/account': UserResource,
    '/webservice/1.0/pub/connect': UserLoginResource,
    '/webservice/1.0/pub/JSONAPI': AuxResource,
    '/webservice/1.0/pub/sales/list': SalesResource,
    '/webservice/1.0/pub/shops/list': ShopsResource,
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
    '/webservice/1.0/pub/crypto/test': CryptoTestResource, # TODO: remove, just for test

    '/webservice/protected/invalidate': InvalidationResource,
}
