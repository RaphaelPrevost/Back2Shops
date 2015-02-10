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
from fouillis.views import admin_required
from notifs.views import *

urlpatterns = patterns(settings.get_site_prefix() + 'notifs',
   url(r'/images/new/$',
       UploadImageView.as_view(), name="upload_email_image"),

   url(r'/$',
       admin_required(NotifListView.as_view()), name="notif_list"),
   url(r'/(?P<page>\d+)$',
       admin_required(NotifListView.as_view()), name="notif_list"),

   url(r'/new$',
       admin_required(NewNotifView.as_view()), name="new_notif"),
   url(r'/(?P<pk>\d+)/edit$',
       admin_required(EditNotifView.as_view()), name="edit_notif"),
   url(r'/(?P<pk>\d+)/delete$',
       admin_required(DeleteNotifView.as_view()), name="delete_notif"),

   url(r'/preview$',
       admin_required(PreviewTemplateContentView.as_view()), name="preview_template"),

)
