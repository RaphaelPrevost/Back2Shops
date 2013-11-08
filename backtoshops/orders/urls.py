import settings
from django.conf.urls.defaults import patterns, url
from orders.views import ShippingFee, CreateShippingView, EditShippingView, ShippingStatusView

urlpatterns = patterns(settings.get_site_prefix()+'orders',
    url(r'/shipping$', CreateShippingView.as_view(), name="shipment_create"),
    url(r'/shipping/edit/(?P<shipping_id>\d+)', EditShippingView.as_view(), name="shipment_edit"),
    url(r'/shipping/status$', ShippingStatusView.as_view(), name="shipment_status"),
    url(r'/shipping/fee', ShippingFee.as_view(), name="shipment_fees"),
)

