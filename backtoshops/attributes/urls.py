import settings
from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from attributes.views import BrandAttributeView
from attributes.views import get_item_attributes

urlpatterns = patterns(settings.get_site_prefix()+'attributes',
    url(r'/brand_attributes/$',
        BrandAttributeView.as_view(),
        name="brand_attributes_view"),
    url(r'/get_item_attrs/(?P<tid>\d+)$',
        login_required(get_item_attributes, login_url="bo_login"),
        name="get_item_attrs"),
)
