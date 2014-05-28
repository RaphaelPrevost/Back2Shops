from webservice.accounts import UserResource
from webservice.auth import UserLoginResource
from webservice.aux import AuxResource
from webservice.cache_invalidation import InvalidationResource
from webservice.crypto import ApiKeyResource
from webservice.orders import OrderDeleteResource
from webservice.orders import OrderDetailResource
from webservice.orders import OrderListResource
from webservice.orders import OrderResource
from webservice.orders import OrderStatusResource
from webservice.orders import ShippingFeeResource
from webservice.payment import PaymentInitResource
from webservice.payment import PaymentFormResource
from webservice.payment import PaypalProcessResource
from webservice.payment import PaypalGatewayResource
from webservice.sales import SalesResource
from webservice.routes import RoutesResource
from webservice.shipment import ShipmentResource
from webservice.shipping import ShippingListResource
from webservice.shipping import ShippingConfResource
from webservice.shipping import ShippingFeesResource
from webservice.shipping import PubShippingListResource
from webservice.shops import ShopsResource
from webservice.types import TypesResource
from webservice.invoice import InvoiceResource
from webservice.invoice import InvoiceGetResource
from webservice.invoice import InvoiceSendResource


urlpatterns = {
    '/webservice/1.0/pub/account': UserResource,
    '/webservice/1.0/pub/connect': UserLoginResource,
    '/webservice/1.0/pub/JSONAPI': AuxResource,
    '/webservice/1.0/pub/sales/list': SalesResource,
    '/webservice/1.0/pub/shipping/conf': ShippingConfResource,
    '/webservice/1.0/pub/shipping/list': PubShippingListResource,
    '/webservice/1.0/pub/shipping/fees': ShippingFeesResource,
    '/webservice/1.0/pub/shops/list': ShopsResource,
    '/webservice/1.0/pub/types/list': TypesResource,
    '/webservice/1.0/pub/order': OrderResource,
    '/webservice/1.0/pub/payment/init': PaymentInitResource,
    '/webservice/1.0/pub/payment/form': PaymentFormResource,
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
    '/webservice/1.0/pub/invoice/request': InvoiceResource,

    '/webservice/protected/invalidate': InvalidationResource,
    '/webservice/protected/shipping/fee': ShippingFeeResource,

    '/webservice/1.0/private/routes/list': RoutesResource,
    '/webservice/1.0/private/order/orders': OrderListResource,
    '/webservice/1.0/private/order/detail': OrderDetailResource,
    '/webservice/1.0/private/order/delete': OrderDeleteResource,
    '/webservice/1.0/private/order/status': OrderStatusResource,
    '/webservice/1.0/private/invoice/get': InvoiceGetResource,
    '/webservice/1.0/private/invoice/send': InvoiceSendResource,

    '/webservice/1.0/protected/shipping/list': ShippingListResource,
    '/webservice/1.0/protected/shipment': ShipmentResource,

    r'/payment/{id_trans}/process': PaypalProcessResource,
    r'/payment/{id_trans}/gateway': PaypalGatewayResource,
}
