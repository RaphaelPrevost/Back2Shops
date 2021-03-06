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
from django.conf.urls import patterns, url
from attributes.views import BrandAttributeView
from attributes.views import get_item_attributes
from attributes.views import get_item_var_attributes
from fouillis.views import operator_upper_required

urlpatterns = patterns(settings.get_site_prefix()+'attributes',
    url(r'/brand_attributes/$',
        BrandAttributeView.as_view(),
        name="brand_attributes_view"),
    url(r'/get_item_attrs/(?P<tid>\d+)$',
        operator_upper_required(get_item_attributes, login_url="bo_login"),
        name="get_item_attrs"),
    url(r'/get_var_item_attrs/(?P<tid>\d+)$',
        operator_upper_required(get_item_var_attributes, login_url="bo_login"),
        name="get_var_item_attrs"),
)
