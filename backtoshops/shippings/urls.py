import settings
from django.conf.urls import patterns, url
from shippings.views import CustomShippingRateView


urlpatterns = patterns(settings.get_site_prefix()+'shippings',
    url(r'/custom_shipping_rate/new/$',
        CustomShippingRateView.as_view(),
        name="add_new_custom_shipping_rate"),
)
