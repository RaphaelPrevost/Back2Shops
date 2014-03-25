import settings
from django.conf.urls.defaults import patterns, url

from fouillis.views import operator_upper_required
from fouillis.views import shop_manager_upper_required
from orders.views import CreateShippingView
from orders.views import EditShippingView
from orders.views import ListOrdersView
from orders.views import OrderDetails
from orders.views import OrderPacking
from orders.views import ShippingFee
from orders.views import ShippingStatusView
from orders.views import OrderDeletePacking
from orders.views import OrderNewPacking
from orders.views import OrderUpdatePacking


urlpatterns = patterns(settings.get_site_prefix()+'orders',
    url(r'/shipping$', CreateShippingView.as_view(), name="shipment_create"),
    url(r'/shipping/edit/(?P<shipping_id>\d+)', EditShippingView.as_view(), name="shipment_edit"),
    url(r'/shipping/status$', ShippingStatusView.as_view(), name="shipment_status"),
    url(r'/shipping/fee', ShippingFee.as_view(), name="shipment_fees"),

    url(r'/list/(?:(?P<orders_type>.+)/)?$',
        operator_upper_required(ListOrdersView.as_view(), login_url="bo_login"),
        name='list_orders'),
    url(r'/details/(?:(?P<order_id>\d+)/)?$',
        OrderDetails.as_view(),
        name='order_details'),
    url(r'/packing/(?:(?P<order_id>\d+)/)?$',
        operator_upper_required(OrderPacking.as_view(), login_url="bo_login"),
        name='order_packing_list'),
    url(r'/new/packing$',
        operator_upper_required(OrderNewPacking.as_view(), login_url="bo_login"),
        name='order_new_shipment'),
    url(r'/update/packing$',
        operator_upper_required(OrderUpdatePacking.as_view(), login_url="bo_login"),
        name='order_update_shipment'),
    url(r'/delete/packing$',
        shop_manager_upper_required(OrderDeletePacking.as_view(),
                                    login_url="bo_login"),
        name='order_delete_shipment'),
)

