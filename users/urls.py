# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © Dragon Dollar Limited
# contact: contact@dragondollar.com
#
# This software is a collection of webservices designed to provide a secure
# and scalable framework to build e-commerce websites.
#
# This software is governed by the CeCILL-B license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL-B
# license as circulated by CEA, CNRS and INRIA at the following URL
# " http://www.cecill.info".
#
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL-B license and that you accept its terms.
#
#############################################################################


from webservice import coupon
from webservice import ticket
from webservice import ticket_attachment
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
from webservice.orders import OrderStatusHandleResource
from webservice.orders import ShippingFeeResource
from webservice.payment import PayboxGatewayResource
from webservice.payment import PaymentFormResource
from webservice.payment import PaymentInitResource
from webservice.payment import PaypalGatewayResource
from webservice.payment import PaypalProcessResource
from webservice.payment import StripeProcessResource
from webservice.routes import RoutesResource
from webservice.sales import SalesResource
from webservice.shipment import ShipmentResource
from webservice.shipping import PubShippingListResource
from webservice.shipping import ShippingConfResource
from webservice.shipping import ShippingFeesResource
from webservice.shipping import ShippingListResource
from webservice.sensor.visitors import SensorVisitorsResource
from webservice.sensor.visitors_log import SensorVisitorsLogResource
from webservice.sensor.visitors_online import SensorVisitorsOnlineResource
from webservice.sensor.incomes import SensorIncomesResource
from webservice.sensor.orders import SensorOrdersResource
from webservice.sensor.bought_history import SensorBoughtHistoryResource
from webservice.shops import ShopsResource
from webservice.slide_show import SlideShowResource
from webservice.suggest import SuggestResource
from webservice.taxes import TaxesResource
from webservice.types import TypesResource
from webservice.vessel.notif import VesselArrivalNotifResource
from webservice.vessel.notif import ContainerArrivalNotifResource
from webservice.vessel.search import SearchContainerResource
from webservice.vessel.search import SearchPortResource
from webservice.vessel.search import SearchVesselResource
from webservice.vessel.user_fleet import UserFleetResource
from webservice.vessel.vessel import VesselDetailResource
from webservice.vessel.vessel import VesselNaviPathResource


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
    '/webservice/1.0/pub/suggest': SuggestResource,
    '/webservice/1.0/pub/brand/home/slideshow': SlideShowResource,
    r'/webservice/1.0/pub/tickets/post': ticket.TicketPost4FUserResource,
    r'/webservice/1.0/pub/tickets/list': ticket.TicketList4FUserResource,
    r'/webservice/1.0/pub/tickets/upload': ticket_attachment.TicketAttachUploadResource,
    r'/webservice/1.0/pub/tickets/read': ticket_attachment.TicketAttachRead4FUserResource,
    r'/webservice/1.0/pub/tickets/rate': ticket.TicketRateResource,

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

    r'/webservice/1.0/private/tickets/post': ticket.TicketPostResource,
    r'/webservice/1.0/private/tickets/list': ticket.TicketListResource,
    r'/webservice/1.0/private/tickets/read': ticket_attachment.TicketAttachReadResource,
    r'/webservice/1.0/private/tickets/prio': ticket.TicketPriorityResource,
    r'/webservice/1.0/private/tickets/lock': ticket.TicketLockResource,
    r'/webservice/1.0/private/tickets/rel': ticket.TicketRelResource,

    '/webservice/1.0/private/sensor/visits': SensorVisitorsResource,
    '/webservice/1.0/private/sensor/income': SensorIncomesResource,
    '/webservice/1.0/private/sensor/orders': SensorOrdersResource,
    '/webservice/1.0/private/sensor/bought_history': SensorBoughtHistoryResource,
    '/webservice/1.0/private/sensor/visitors_online': SensorVisitorsOnlineResource,
    '/webservice/1.0/private/sensor/visitors/log': SensorVisitorsLogResource,
    '/webservice/1.0/private/coupon': coupon.CouponPostResource,
    '/webservice/1.0/private/coupon/list': coupon.CouponListResource,
    '/webservice/1.0/public/coupon/redeem': coupon.CouponRedeemResource,

    '/webservice/1.0/protected/shipping/list': ShippingListResource,
    '/webservice/1.0/protected/shipment': ShipmentResource,
    '/webservice/1.0/protected/order_status': OrderStatusHandleResource,

    '/webservice/1.0/protected/container/search': SearchContainerResource,
    '/webservice/1.0/protected/port/search': SearchPortResource,
    '/webservice/1.0/protected/vessel/details': VesselDetailResource,
    '/webservice/1.0/protected/vessel/path': VesselNaviPathResource,
    '/webservice/1.0/protected/vessel/search': SearchVesselResource,
    '/webservice/1.0/private/container/reminder': ContainerArrivalNotifResource,
    '/webservice/1.0/private/vessel/reminder': VesselArrivalNotifResource,
    '/webservice/1.0/private/user_fleet': UserFleetResource,

    r'/payment/paypal/{id_trans}/process': PaypalProcessResource,
    r'/payment/paypal/{id_trans}/gateway': PaypalGatewayResource,

    r'/payment/paybox/{id_trans}/gateway': PayboxGatewayResource,

    r'/payment/stripe/{id_trans}/process': StripeProcessResource,
}
