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


import json
import settings

from brandings.forms import BrandingForm
from brandings.models import Branding
from common.admin_view import BaseAdminView

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView


class BaseBrandingView(BaseAdminView):
    template_name = "branding.html"
    form_class = BrandingForm
    model = Branding

    def get_initial(self):
        return {'brand': self.brand()}

    def get_queryset(self):
        return Branding.objects.filter(for_brand=self.brand())

class CreateBrandingView(BaseBrandingView, CreateView):
    def get_success_url(self):
        return reverse('edit_branding',args=[self.object.id])

class EditBrandingView(BaseBrandingView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_branding",args=[pk])

class DeleteBrandingView(BaseBrandingView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(
            content=json.dumps({"branding_pk": self.kwargs.get('pk', None)}),
            mimetype="application/json")

