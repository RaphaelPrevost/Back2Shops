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
import json
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView
from common.admin_view import BaseAdminView

from attributes.models import CommonAttribute
from producttypes.forms import ProductTypeForm
from backend.forms import SACommonAttributeForm
from sales.models import ProductType

class BaseProductTypeView(BaseAdminView):
    template_name = "product_type.html"
    form_class = ProductTypeForm
    model = ProductType
    formset = inlineformset_factory(ProductType, CommonAttribute,
                                    form=SACommonAttributeForm, extra=0)

    def get_queryset(self):
        qs = super(BaseProductTypeView, self).get_queryset()
        return qs.filter(brand=self.brand()).order_by('sort_order')

    def get_context_data(self, **kwargs):
        kwargs.update({"formset": self.formset})
        return super(BaseProductTypeView, self).get_context_data(**kwargs)

    def get_initial(self):
        return {'brand': self.brand()}

class CreateProductTypeView(BaseProductTypeView, CreateView):
    def get_success_url(self):
        return reverse('edit_producttype', args=[self.object.id])

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            product_type=form.save(commit=False)
            formset = self.formset(data=self.request.POST, instance=product_type)
            if formset.is_valid():
                form.save(commit=True)
                formset.save()
                return self.form_valid(form)
        return self.form_invalid(form)

class EditProductTypeView(BaseProductTypeView, UpdateView):
    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse("edit_producttype",args=[pk])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.formset = self.formset(instance=self.get_object())
        return super(EditProductTypeView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            product_type = form.save(commit=False)
            formset = self.formset(data=self.request.POST, instance=product_type)
            if formset.is_valid():
                form.save(commit=True)
                formset.save()
                return self.form_valid(form)
        return self.form_invalid(form)

class DeleteProductTypeView(BaseProductTypeView, DeleteView):
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        content = {"attribute_pk": self.kwargs.get('pk', None)}
        self.object.delete()
        if self.object.products.all():
            content.update({'reprieve': True, 'name': self.object.name})
        return HttpResponse(content=json.dumps(content),
                            mimetype="application/json")

class UpdateProductTypeOrderView(BaseAdminView, View):
    def post(self, *args, **kwargs):
        sorted_attrs = json.loads(self.request.POST.get('sorted', '{}'))
        for attr in sorted_attrs:
            obj = ProductType.objects.get(pk=attr.replace('attribute_', ''))
            obj.sort_order = sorted_attrs[attr]
            obj.save()
        content = {'success': True}
        return HttpResponse(content=json.dumps(content),
                            mimetype="application/json")

