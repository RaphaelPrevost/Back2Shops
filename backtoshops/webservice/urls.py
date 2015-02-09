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


import settings
from django.conf.urls.defaults import patterns, url
from fouillis.views import manager_required
from webservice.views import SalesListView, BrandInfoView, BrandListView, \
    SalesInfoView, ShopsInfoView, ShopsListView, TypesInfoView, TypesListView, \
    VicinityShopsListView, VicinitySalesListView, \
    authenticate, barcode_increment, barcode_decrement, barcode_returned, \
    BrandingsListView, apikey, SalesFindView, TaxesListView, ShippingInfoView, \
    ShippingFeesView, ShippingServicesInfoView, InvoiceView, \
    payment_init, RoutesListView, SuggestView, EventListView, event_push




urlpatterns = patterns(settings.SITE_NAME,
    url(r'1.0/pub/sales/list', SalesListView.as_view()),
    url(r'1.0/pub/shops/list', ShopsListView.as_view()),
    url(r'1.0/pub/types/list/(?P<brand>\d+)', TypesListView.as_view()),
    url(r'1.0/pub/brand/list', BrandListView.as_view()),
    url(r'1.0/pub/brand/home/slideshow/(?P<brand>\d+)', BrandingsListView.as_view()),
    url(r'1.0/pub/brand/info/(?P<pk>\d+)', BrandInfoView.as_view()),
    url(r'1.0/pub/sales/info/(?P<pk>\d+)', SalesInfoView.as_view()),
    url(r'1.0/pub/shops/info/(?P<pk>\d+)', ShopsInfoView.as_view()),
    url(r'1.0/pub/types/info/(?P<pk>\d+)', TypesInfoView.as_view()),
    url(r'1.0/pub/sales/find', SalesFindView.as_view()),
    url(r'1.0/pub/apikey.pem', apikey),

    url(r'1.0/protected/shipping/fees', ShippingFeesView.as_view()),

    url(r'1.0/private/auth', authenticate),
    url(r'1.0/private/event/list', EventListView.as_view()),
    url(r'1.0/private/event/push', event_push),
    url(r'1.0/private/payment/init', payment_init),
    url(r'1.0/private/routes/list', RoutesListView.as_view()),
    url(r'1.0/private/stock/inc', barcode_increment),
    url(r'1.0/private/stock/dec', barcode_decrement),
    url(r'1.0/private/stock/ret', barcode_returned),
    url(r'1.0/private/taxes/get', TaxesListView.as_view()),
    url(r'1.0/private/shipping/info', ShippingInfoView.as_view()),
    url(r'1.0/private/shipping/services/info', ShippingServicesInfoView.as_view()),
    url(r'1.0/private/invoice/get', InvoiceView.as_view()),
    url(r'1.0/private/suggest', SuggestView.as_view()),
    url(r'1.0/vicinity/shops', VicinityShopsListView.as_view()),
    url(r'1.0/vicinity/sales', VicinitySalesListView.as_view()),
)
