import settings
from django.conf.urls.defaults import patterns, url
from webservice.views import SalesListView, BrandInfoView, BrandListView, SalesInfoView, ShopsInfoView, ShopsListView, TypesInfoView, TypesListView, \
                             VicinityShopsListView, VicinitySalesListView, \
                             authenticate, barcode_increment, barcode_decrement, barcode_returned, \
                             BrandingsListView, apikey, SalesFindView, TaxesListView, ShippingInfoView, \
                             ShippingFeesView, ShippingServicesInfoView, InvoiceView, \
                             payment_init, RoutesListView




urlpatterns = patterns(settings.SITE_NAME,
    url(r'1.0/pub/sales/list', SalesListView.as_view()),
    url(r'1.0/pub/shops/list', ShopsListView.as_view()),
    url(r'1.0/pub/types/list', TypesListView.as_view()),
    url(r'1.0/pub/brand/list', BrandListView.as_view()),
    url(r'1.0/pub/brand/home/slideshow', BrandingsListView.as_view()),
    url(r'1.0/pub/brand/info/(?P<pk>\d+)', BrandInfoView.as_view()),
    url(r'1.0/pub/sales/info/(?P<pk>\d+)', SalesInfoView.as_view()),
    url(r'1.0/pub/shops/info/(?P<pk>\d+)', ShopsInfoView.as_view()),
    url(r'1.0/pub/types/info/(?P<pk>\d+)', TypesInfoView.as_view()),
    url(r'1.0/pub/sales/find', SalesFindView.as_view()),
    url(r'1.0/pub/apikey.pem', apikey),

    url(r'1.0/protected/shipping/fees', ShippingFeesView.as_view()),

    url(r'1.0/private/auth',      authenticate),
    url(r'1.0/private/payment/init', payment_init),
    url(r'1.0/private/routes/list', RoutesListView.as_view()),
    url(r'1.0/private/stock/inc', barcode_increment),
    url(r'1.0/private/stock/dec', barcode_decrement),
    url(r'1.0/private/stock/ret', barcode_returned),
    url(r'1.0/private/taxes/get', TaxesListView.as_view()),
    url(r'1.0/private/shipping/info', ShippingInfoView.as_view()),
    url(r'1.0/private/shipping/services/info', ShippingServicesInfoView.as_view()),
    url(r'1.0/private/invoice/get', InvoiceView.as_view()),
    url(r'1.0/vicinity/shops',    VicinityShopsListView.as_view()),
    url(r'1.0/vicinity/sales',    VicinitySalesListView.as_view()),
)
