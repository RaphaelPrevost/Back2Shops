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
import json
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.http import HttpResponse
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from fouillis.views import AdminLoginRequiredMixin
from routes.models import HtmlMeta, Route, RouteParam
from routes.forms import RouteForm, HTMLMetasForm, RouteParamForm


class BaseRouteView(AdminLoginRequiredMixin):
    template_name = "route.html"
    model = Route
    form_class = RouteForm
    meta_form = inlineformset_factory(Route, HtmlMeta, form=HTMLMetasForm, extra=0)
    routeparam_form = inlineformset_factory(Route, RouteParam, form=RouteParamForm, extra=0)

    def get_success_url(self):
        return reverse("routes")

    def get_context_data(self, **kwargs):
        routes = self.get_routes()

        try:
            p_size = int(self.request.GET.get('page_size', settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass

        self.current_page = int(self.kwargs.get('page', '1'))
        paginator = Paginator(routes, settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages

        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)
        kwargs.update({
            'pk': self.kwargs.get('pk', None),
            'routes': self.page,
            'meta_form': self.meta_form,
            'routeparam_form': self.routeparam_form,
            'request': self.request
        })
        return kwargs

    def get_form_kwargs(self):
        kwargs = super(BaseRouteView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_routes(self):
        return Route.objects.all()


class CreateRouteView(BaseRouteView, CreateView):
    form_class = RouteForm

    def get_initial(self):
        if self.request.user.is_superuser:
            return {}

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            route = form.save(commit=False)
            meta_form = self.meta_form(data=self.request.POST, instance=route)
            routeparam_form = self.routeparam_form(data=self.request.POST, instance=route)

            if meta_form.is_valid() and routeparam_form.is_valid():
                form.save(commit=True)
                meta_form.save()
                routeparam_form.save()
                return self.form_valid(form)

        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('edit_route', args=[self.object.id])


class EditRouteView(BaseRouteView, UpdateView):
    form_class = RouteForm

    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse('edit_route', args=[pk])

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.meta_form = self.meta_form(instance=self.get_object())
        self.routeparam_form = self.routeparam_form(instance=self.get_object())

        return super(BaseRouteView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            route = form.save(commit=False)
            meta_form = self.meta_form(data=self.request.POST, instance=route)
            routeparam_form = self.routeparam_form(data=self.request.POST, instance=route)

            if meta_form.is_valid() and routeparam_form.is_valid():
                form.save(commit=True)
                meta_form.save()
                routeparam_form.save()
                return self.form_valid(form)

        return self.form_invalid(form)


class DeleteRouteView(BaseRouteView, DeleteView):

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({'pk': self.kwargs.get('pk', None)}),
                            mimetype="application/json")


def get_route_params(request, *args, **kwargs):
    route_id = kwargs.get('pid', None)

    routeParam = RouteParam.objects.filter(route=route_id)
    datas = [(x.pk, x.name, x.is_required) for x in routeParam]
    return HttpResponse(json.dumps(datas), mimetype='application/json')


def get_page_roles(request, *args, **kwargs):
    term = request.GET.get('term', None)

    if not term:
        return HttpResponse(json.dumps(''))

    datas = [({'value': x.get('page_role')}) for x in Route.objects.values('page_role').filter(page_role__icontains=term).distinct()]
    return HttpResponse(json.dumps(datas), mimetype='application/json')

