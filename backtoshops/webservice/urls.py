import settings
from django.conf.urls.defaults import patterns, url
from webservice.views import SalesListView, BrandInfoView, BrandListView, SalesInfoView, ShopsInfoView, ShopsListView, TypesInfoView, TypesListView, authenticate, barcode_increment, barcode_decrement, barcode_returned

urlpatterns = patterns(settings.SITE_NAME,
    url(r'1.0/pub/sales/list', SalesListView.as_view()),
    url(r'1.0/pub/shops/list', ShopsListView.as_view()),
    url(r'1.0/pub/types/list', TypesListView.as_view()),
    url(r'1.0/pub/brand/list', BrandListView.as_view()),
    url(r'1.0/pub/brand/info/(?P<pk>\d+)', BrandInfoView.as_view()),
    url(r'1.0/pub/sales/info/(?P<pk>\d+)', SalesInfoView.as_view()),
    url(r'1.0/pub/shops/info/(?P<pk>\d+)', ShopsInfoView.as_view()),
    url(r'1.0/pub/types/info/(?P<pk>\d+)', TypesInfoView.as_view()),
    
	url(r'1.0/private/auth',      authenticate),
    url(r'1.0/private/stock/inc', barcode_increment),
    url(r'1.0/private/stock/dec', barcode_decrement),
    url(r'1.0/private/stock/ret', barcode_returned),
)