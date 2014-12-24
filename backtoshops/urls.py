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


from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from accounts.views import home_page
from fouillis.views import operator_upper_required
import settings
from init import monkey_patch
monkey_patch()

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = staticfiles_urlpatterns()
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
   )

if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        url(r'^rosetta/', include('rosetta.urls')),
    )

urlpatterns += patterns('',
    url(r'^logout$', 'django.contrib.auth.views.logout', name='bo_logout')
)

urlpatterns += patterns('',
    url(r'^emails', include(settings.get_site_prefix()+'emails.urls')),
    url(r'^routes', include(settings.get_site_prefix()+'routes.urls')),
    url(r'^webservice', include(settings.get_site_prefix()+'webservice.urls')),
    url(r'^attributes', include(settings.get_site_prefix()+'attributes.urls')),
    url(r'^pictures', include(settings.get_site_prefix()+'pictures.urls')),
    url(r'^sales', include(settings.get_site_prefix()+'sales.urls')),
    url(r'^shops', include(settings.get_site_prefix()+'shops.urls')),
    url(r'^orders', include(settings.get_site_prefix()+'orders.urls')),
    url(r'^login', 'fouillis.views.login_staff', name='bo_login'),
    url(r'^$',
        operator_upper_required(home_page, login_url="bo_login"),
        name='bo_index'),
    # Examples:
    # url(r'^$', 'backtoshops.views.home', name='home'),
    # url(r'^backtoshops/', include('backtoshops.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^setlang/',settings.get_site_prefix()+'accounts.views.set_language'),
    url(r'^sa/', include(settings.get_site_prefix()+'backend.urls')),
    url(r'^accounts/', include(settings.get_site_prefix()+'accounts.urls')),
    url(r'^shippings', include(settings.get_site_prefix()+'shippings.urls')),
    url(r'^taxes', include(settings.get_site_prefix()+'taxes.urls')),
    url(r'^countries', include(settings.get_site_prefix()+'countries.urls')),
    url(r'^promotion', include(settings.get_site_prefix()+'promotion.urls')),
    url(r'^stats', include(settings.get_site_prefix()+'stats.urls')),
    url(r'^brandings', include(settings.get_site_prefix()+'brandings.urls')),
    url(r'^categories', include(settings.get_site_prefix()+'categories.urls')),
    url(r'^producttypes', include(settings.get_site_prefix()+'producttypes.urls')),
    url(r'^termsandconditions', include(settings.get_site_prefix()+'termsandconditions.urls')),
)
