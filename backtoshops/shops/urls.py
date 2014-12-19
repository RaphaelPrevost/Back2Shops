# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@…, contact@…
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
from django.core.urlresolvers import reverse
from shops.views import ShopCoordinates, CreateShopView, DeleteShopView, EditShopView

urlpatterns = patterns(settings.get_site_prefix()+'shops',
    url(r'/$', CreateShopView.as_view(), name="page_shops"),
    url(r'/(?P<page>\d+)$', CreateShopView.as_view()),
    url(r'/(?P<pk>\d+)/edit$', EditShopView.as_view(), name="edit_shop"),
    url(r'/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditShopView.as_view()),
    url(r'/(?P<pk>\d+)/delete$', DeleteShopView.as_view(), name="delete_shop"),
    url(r'/coordinates', ShopCoordinates.as_view(), name='shop_coordinates'),
)

    # url(r'/shop/(?:(?P<shop_id>\d+)/)?$', 
    #     ShopView.as_view(),
    #     name="shop"
    # ),
    # url(r'/shop/(?P<shop_id>\d+)/$',
    #     DeleteView.as_view(model=Shop, success_url=reverse("shop")),
    #     name="delete_shop"
    # ),
