import settings
from django.conf.urls.defaults import patterns, url
from views import BrandAttributeView

urlpatterns = patterns(settings.get_site_prefix()+'attributes',
    url(r'/brand_attributes/$',
        BrandAttributeView.as_view(),
        name="brand_attributes_view"),
)
