import settings
from django.conf.urls.defaults import patterns, url
from django.contrib.auth.decorators import login_required

from orders.views import CreateShippingView
from orders.views import EditShippingView
from orders.views import ListOrdersView
from orders.views import OrderDetails
from orders.views import ShippingFee
from orders.views import ShippingStatusView


urlpatterns = patterns(settings.get_site_prefix()+'orders',
    url(r'/shipping$', CreateShippingView.as_view(), name="shipment_create"),
    url(r'/shipping/edit/(?P<shipping_id>\d+)', EditShippingView.as_view(), name="shipment_edit"),
    url(r'/shipping/status$', ShippingStatusView.as_view(), name="shipment_status"),
    url(r'/shipping/fee', ShippingFee.as_view(), name="shipment_fees"),

    url(r'/list/(?:(?P<orders_type>.+)/)?$',
        login_required(ListOrdersView.as_view(), login_url="bo_login"),
        name='list_orders'),
    url(r'/details/(?:(?P<order_id>\d+)/)?$',
        OrderDetails.as_view(),
        name='order_details'),
)

