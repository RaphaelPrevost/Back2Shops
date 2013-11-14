from webservice.accounts import UserResource
from webservice.auth import UserLoginResource
from webservice.aux import AuxResource
from webservice.cache_invalidation import InvalidationResource
from webservice.crypto import ApiKeyResource
from webservice.crypto import CryptoTestResource
from webservice.orders import OrderDeleteResource
from webservice.orders import OrderDetailResource
from webservice.orders import OrderListResource
from webservice.orders import OrderResource
from webservice.orders import OrderStatusResource
from webservice.orders import ShippingFeeResource
from webservice.sales import SalesResource
from webservice.shops import ShopsResource


urlpatterns = {
    '/webservice/1.0/pub/account': UserResource,
    '/webservice/1.0/pub/connect': UserLoginResource,
    '/webservice/1.0/pub/JSONAPI': AuxResource,
    '/webservice/1.0/pub/sales/list': SalesResource,
    '/webservice/1.0/pub/shops/list': ShopsResource,
    '/webservice/1.0/pub/order': OrderResource,
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
    '/webservice/1.0/pub/crypto/test': CryptoTestResource, # TODO: remove, just for test

    '/webservice/protected/invalidate': InvalidationResource,
    '/webservice/protected/shipping/fee': ShippingFeeResource,

    '/webservice/1.0/private/order/orders': OrderListResource,
    '/webservice/1.0/private/order/detail': OrderDetailResource,
    '/webservice/1.0/private/order/delete': OrderDeleteResource,
    '/webservice/1.0/private/order/status': OrderStatusResource,

}
