from webservice.accounts import UserResource
from webservice.auth import UserLoginResource
from webservice.auth import UserVerifyResource
from webservice.aux import AuxResource
from webservice.cache_invalidation import InvalidationResource
from webservice.crypto import ApiKeyResource
from webservice.invoice import InvoiceGet4FUserResource
from webservice.invoice import InvoiceGetResource
from webservice.invoice import InvoiceResource
from webservice.invoice import InvoiceSendResource
from webservice.orders import OrderDeleteResource
from webservice.orders import OrderDetailResource
from webservice.orders import OrderDetail4FUserResource
from webservice.orders import OrderListResource
from webservice.orders import OrderList4FUserResource
from webservice.orders import OrderResource
from webservice.orders import OrderStatusResource
from webservice.orders import ShippingFeeResource
from webservice.payment import PayboxGatewayResource
from webservice.payment import PaymentFormResource
from webservice.payment import PaymentInitResource
from webservice.payment import PaypalGatewayResource
from webservice.payment import PaypalProcessResource
from webservice.routes import RoutesResource
from webservice.sales import SalesResource
from webservice.shipment import ShipmentResource
from webservice.shipping import PubShippingListResource
from webservice.shipping import ShippingConfResource
from webservice.shipping import ShippingFeesResource
from webservice.shipping import ShippingListResource
from webservice.sensor.visitors import SensorVisitorsResource
from webservice.sensor.incomes import SensorIncomesResource
from webservice.sensor.orders import SensorOrdersResource
from webservice.shops import ShopsResource
from webservice.taxes import TaxesResource
from webservice.types import TypesResource
from webservice.vessel.search import SearchPortResource
from webservice.vessel.search import SearchVesselResource
from webservice.vessel.vessel import VesselDetailResource


urlpatterns = {
    '/webservice/1.0/pub/account': UserResource,
    '/webservice/1.0/pub/connect': UserLoginResource,
    '/webservice/1.0/pub/online': UserVerifyResource,
    '/webservice/1.0/pub/JSONAPI': AuxResource,
    '/webservice/1.0/pub/sales/list': SalesResource,
    '/webservice/1.0/pub/shipping/conf': ShippingConfResource,
    '/webservice/1.0/pub/shipping/list': PubShippingListResource,
    '/webservice/1.0/pub/shipping/fees': ShippingFeesResource,
    '/webservice/1.0/pub/shops/list': ShopsResource,
    '/webservice/1.0/pub/types/list': TypesResource,
    '/webservice/1.0/pub/order': OrderResource,
    '/webservice/1.0/pub/order/orders': OrderList4FUserResource,
    '/webservice/1.0/pub/order/detail': OrderDetail4FUserResource,
    '/webservice/1.0/pub/invoice/get': InvoiceGet4FUserResource,
    '/webservice/1.0/pub/payment/init': PaymentInitResource,
    '/webservice/1.0/pub/payment/form': PaymentFormResource,
    '/webservice/1.0/pub/apikey.pem': ApiKeyResource,
    '/webservice/1.0/pub/invoice/request': InvoiceResource,

    '/webservice/protected/invalidate': InvalidationResource,
    '/webservice/protected/shipping/fee': ShippingFeeResource,

    '/webservice/1.0/private/routes/list': RoutesResource,
    '/webservice/1.0/private/taxes/list': TaxesResource,
    '/webservice/1.0/private/order/orders': OrderListResource,
    '/webservice/1.0/private/order/detail': OrderDetailResource,
    '/webservice/1.0/private/order/delete': OrderDeleteResource,
    '/webservice/1.0/private/order/status': OrderStatusResource,
    '/webservice/1.0/private/invoice/get': InvoiceGetResource,
    '/webservice/1.0/private/invoice/send': InvoiceSendResource,

    '/webservice/1.0/private/sensor/visits': SensorVisitorsResource,
    '/webservice/1.0/private/sensor/incomes': SensorIncomesResource,
    '/webservice/1.0/private/sensor/orders': SensorOrdersResource,

    '/webservice/1.0/protected/shipping/list': ShippingListResource,
    '/webservice/1.0/protected/shipment': ShipmentResource,

    '/webservice/1.0/protected/vessel/search': SearchVesselResource,
    '/webservice/1.0/protected/port/search': SearchPortResource,
    '/webservice/1.0/protected/vessel/details': VesselDetailResource,

    r'/payment/paypal/{id_trans}/process': PaypalProcessResource,
    r'/payment/paypal/{id_trans}/gateway': PaypalGatewayResource,

    r'/payment/paybox/{id_trans}/gateway': PayboxGatewayResource,
}
