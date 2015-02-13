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

from fouillis.views import operator_upper_required
from fouillis.views import shop_manager_upper_required
from orders.views import CreateShippingView
from orders.views import EditShippingView
from orders.views import ListOrdersView
from orders.views import OrderDelete
from orders.views import OrderDetails
from orders.views import OrderPacking
from orders.views import OrderVenteView
from orders.views import PackingFeeView
from orders.views import ShippingFee
from orders.views import ShippingStatusView
from orders.views import OrderDeletePacking
from orders.views import OrderInvoices
from orders.views import OrderNewPacking
from orders.views import OrderUpdatePacking
from orders.views import SendInvoices


urlpatterns = patterns(settings.get_site_prefix()+'orders',
    url(r'/shipping$', CreateShippingView.as_view(), name="shipment_create"),
    url(r'/shipping/edit/(?P<shipping_id>\d+)', EditShippingView.as_view(), name="shipment_edit"),
    url(r'/shipping/status$', ShippingStatusView.as_view(), name="shipment_status"),
    url(r'/shipping/fee', ShippingFee.as_view(), name="shipment_fees"),

    url(r'/list/(?:(?P<orders_type>.+)/)?$',
        operator_upper_required(ListOrdersView.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='list_orders'),
    url(r'/vente/(?:(?P<orders_type>.+)/)?$',
        operator_upper_required(OrderVenteView.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_vente'),
    url(r'/details/(?:(?P<order_id>\d+)/)?$',
        operator_upper_required(OrderDetails.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_details'),
    url(r'/delete/(?P<order_id>\d+)$',
        operator_upper_required(OrderDelete.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_delete'),
    url(r'/packing/(?:(?P<order_id>\d+)/)?$',
        operator_upper_required(OrderPacking.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_packing_list'),
    url(r'/new/packing$',
        operator_upper_required(OrderNewPacking.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_new_shipment'),
    url(r'/update/packing$',
        operator_upper_required(OrderUpdatePacking.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_update_shipment'),
    url(r'/delete/packing$',
        shop_manager_upper_required(OrderDeletePacking.as_view(),
                                    login_url="bo_login",
                                    super_allowed=False),
        name='order_delete_shipment'),
    url(r'/invoices/(?P<order_id>\d+)/(?P<shipment>\d+)/$',
        operator_upper_required(OrderInvoices.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='order_invoices_list'),
    url(r'/send/invoices',
        operator_upper_required(SendInvoices.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='send_invoices'),
    url(r'/packing/fee',
        operator_upper_required(PackingFeeView.as_view(),
                                login_url="bo_login",
                                super_allowed=False),
        name='packing_fee'),
)

