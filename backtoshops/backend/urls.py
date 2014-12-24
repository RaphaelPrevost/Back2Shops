# -*- coding: utf-8 -*-

#############################################################################
#
# Copyright © BGA SARL and Dragon Dollar Limited
# contact: contact@lbga.fr, contact@dragondollar.com
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
from django.conf.urls import patterns
from django.conf.urls import url
from backend.views import *

urlpatterns = patterns(settings.get_site_prefix()+'backend',
    url(r'brands/$', CreateBrandView.as_view(), name='sa_brands'),
    url(r'brands/(?P<page>\d+)$', CreateBrandView.as_view()),
    url(r'brands/(?P<pk>\d+)/edit/$', EditBrandView.as_view(), name='sa_edit_brand'),
    url(r'brands/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditBrandView.as_view()),
    url(r'brands/(?P<pk>\d+)/delete/$', DeleteBrandView.as_view(), name='sa_delete_brand'),
    url(r'users/$', CreateUserView.as_view(), name='sa_users'),
    url(r'users/(?P<pk>\d+)/edit/$', EditUserView.as_view(), name='sa_edit_user'),
    url(r'users/(?P<pk>\d+)/delete/$', DeleteUserView.as_view(), name='sa_delete_user'),
    url(r'ajax/user_search/$',ajax_user_search, name='sa_ajax_user_search'),
    url(r'settings/$', settings_view, name='sa_settings' ),

    url(r'carriers/$', CreateCarrierView.as_view(), name='sa_carriers'),
    url(r'carriers/(?P<page>\d+)$', CreateCarrierView.as_view()),
    url(r'carriers/(?P<pk>\d+)/edit/$', EditCarrierView.as_view(), name='sa_edit_carrier'),
    url(r'carriers/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditCarrierView.as_view()),
    url(r'carriers/(?P<pk>\d+)/delete/$', DeleteCarrierView.as_view(), name='sa_delete_carrier'),

    url(r'taxes/$', CreateTaxView.as_view(), name='sa_taxes'),
    url(r'taxes/(?P<page>\d+)$', CreateTaxView.as_view()),
    url(r'taxes/(?P<pk>\d+)/edit/$', EditTaxView.as_view(), name='sa_edit_tax'),
    url(r'taxes/(?P<pk>\d+)/edit/(?P<page>\d+)$', EditTaxView.as_view()),
    url(r'taxes/(?P<pk>\d+)/delete/$', DeleteTaxView.as_view(), name='sa_delete_tax'),

)
