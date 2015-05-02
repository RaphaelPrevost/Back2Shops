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
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import View, ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.base import TemplateResponseMixin
from sorl.thumbnail import get_thumbnail

from fouillis.views import AdminLoginRequiredMixin
from notifs.forms import NotifForm
from notifs.models import Notif, NotifTemplateImage


class NotifListView(AdminLoginRequiredMixin, ListView):
    template_name = "notif_list.html"
    model = Notif
    form_class = NotifForm
    paginate_by = settings.DEFAULT_PAGE_SIZE

    def get_queryset(self):
        queryset = self.model.objects.filter(
                mother_brand=self.request.user.get_profile().work_for)
        if getattr(self, 'search', None):
            queryset = queryset.filter(name__icontains=self.search)
        return queryset

    def post(self, request, *args, **kwargs):
        self.search = self.request.POST.get('search')
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(NotifListView, self).get_context_data(**kwargs)
        context.update({
            'search': getattr(self, 'search', None) or '',
        })
        return context


class NewNotifView(AdminLoginRequiredMixin, CreateView):
    model = Notif
    form_class = NotifForm
    template_name = "notif.html"

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            notif = form.save(commit=True)
            pp_pks = [int(pp['pk']) for pp in form.images.cleaned_data
                                    if not pp['DELETE']]
            notif.images = NotifTemplateImage.objects.filter(pk__in=pp_pks)
            notif.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(NewNotifView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_success_url(self):
        return reverse('notif_list')


class EditNotifView(AdminLoginRequiredMixin, UpdateView):
    model = Notif
    form_class = NotifForm
    template_name = "notif.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(EditNotifView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            notif = form.save(commit=True)
            pp_pks = [int(pp['pk']) for pp in form.images.cleaned_data
                                    if not pp['DELETE']]
            notif.images = NotifTemplateImage.objects.filter(pk__in=pp_pks)
            notif.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse('edit_notif', args=[pk])

    def get_form_kwargs(self):
        kwargs = super(EditNotifView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EditNotifView, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs.get('pk', None)
        return context


class PreviewTemplateContentView(AdminLoginRequiredMixin, CreateView):
    model = Notif
    form_class = NotifForm
    template_name = "template_editor.html"

    def get_form_kwargs(self):
        kwargs = super(CreateView, self).get_form_kwargs()

        initial = {}
        images = []
        for _img in NotifTemplateImage.objects.all():
            images.append({
                'pk': _img.pk,
                'url': _img.image.url,
                'thumb_url': get_thumbnail(_img.image, '40x43').url,
            })
        initial.update({'images': images})
        kwargs.update({'initial': initial})
        return kwargs


class DeleteNotifView(AdminLoginRequiredMixin, DeleteView):
    model = Notif
    form_class = NotifForm

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({'pk': self.kwargs.get('pk', None)}),
                            mimetype="application/json")


class UploadImageView(TemplateResponseMixin, View):
    template_name = ""

    def post(self, request, *args, **kwargs):
        if request.FILES:
            new_img = request.FILES[u'files[]']
            if new_img.size > settings.SALE_IMG_UPLOAD_MAX_SIZE:
                content = {'status': 'max_limit_error'}
                return HttpResponse(json.dumps(content), mimetype='application/json')

            new_media = NotifTemplateImage(image=request.FILES[u'files[]'])
            new_media.save()
            thumb = get_thumbnail(new_media.image, '40x43')
            to_ret = {
                'status': 'ok',
                'pk': new_media.pk,
                'url': new_media.image.url,
                'thumb_url': thumb.url,
            }
            return HttpResponse(json.dumps(to_ret), mimetype="application/json")
        raise HttpResponseBadRequest(_("Please upload a picture."))

