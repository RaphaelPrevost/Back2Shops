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
from django.http import HttpResponse
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.base import View
from sorl.thumbnail import get_thumbnail

from fouillis.views import AdminLoginRequiredMixin
from emails.forms import EmailTemplateForm
from emails.models import EmailTemplate, EmailTemplateImage

class BaseView(AdminLoginRequiredMixin):
    template_name = "email_template.html"
    model = EmailTemplate
    form_class = EmailTemplateForm

    def get_context_data(self, **kwargs):
        templates = EmailTemplate.objects.all()

        try:
            p_size = int(self.request.GET.get('page_size',
                         settings.get_page_size(self.request)))
            p_size = p_size if p_size in settings.CHOICE_PAGE_SIZE \
                            else settings.DEFAULT_PAGE_SIZE
            self.request.session['page_size'] = p_size
        except:
            pass

        self.current_page = int(self.request.GET.get('page')
                             or self.kwargs.get('page', '1'))
        paginator = Paginator(templates, settings.get_page_size(self.request))
        try:
            self.page = paginator.page(self.current_page)
        except(EmptyPage, InvalidPage):
            self.page = paginator.page(paginator.num_pages)
            self.current_page = paginator.num_pages

        self.range_start = self.current_page - (self.current_page % settings.PAGE_NAV_SIZE)
        kwargs.update({
            'pk': self.kwargs.get('pk', 0),
            'choice_page_size': settings.CHOICE_PAGE_SIZE,
            'current_page_size': settings.get_page_size(self.request),
            'prev_10': self.current_page-settings.PAGE_NAV_SIZE
                       if self.current_page-settings.PAGE_NAV_SIZE > 1 else 1,
            'next_10': self.current_page+settings.PAGE_NAV_SIZE
                       if self.current_page+settings.PAGE_NAV_SIZE <= self.page.paginator.num_pages
                       else self.page.paginator.num_pages,
            'page_nav': self.page.paginator.page_range[self.range_start:self.range_start+settings.PAGE_NAV_SIZE],
            'templates': self.page,
            'request': self.request,
            'sale_img_upload_max_size': settings.SALE_IMG_UPLOAD_MAX_SIZE,
        })
        return kwargs

    def get_success_url(self):
        return reverse("new_template")


class NewTemplateView(BaseView, CreateView):

    def post(self, request, *args, **kwargs):
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            email = form.save(commit=True)
            pp_pks = [int(pp['pk']) for pp in form.images.cleaned_data
                                    if not pp['DELETE']]
            email.images = EmailTemplateImage.objects.filter(pk__in=pp_pks)
            email.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse('edit_template', args=[self.object.id])


class EditTemplateView(BaseView, UpdateView):

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(EditTemplateView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        if form.is_valid():
            email = form.save(commit=True)
            pp_pks = [int(pp['pk']) for pp in form.images.cleaned_data
                                    if not pp['DELETE']]
            email.images = EmailTemplateImage.objects.filter(pk__in=pp_pks)
            email.save()
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs.get('pk', None)
        return reverse('edit_template', args=[pk])


class PreviewTemplateContentView(CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = "_email_content.html"

    def get_form_kwargs(self):
        kwargs = super(CreateView, self).get_form_kwargs()

        initial = {}
        images = []
        for _img in EmailTemplateImage.objects.all():
            images.append({
                'pk': _img.pk,
                'url': _img.image.url,
                'thumb_url': get_thumbnail(_img.image, '40x43').url,
            })
        initial.update({'images': images})
        kwargs.update({'initial': initial})
        return kwargs


class DeleteTemplateView(BaseView, DeleteView):

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse(content=json.dumps({'pk': self.kwargs.get('pk', None)}),
                            mimetype="application/json")


class UploadEmailImageView(TemplateResponseMixin, View):
    template_name = ""

    def post(self, request, *args, **kwargs):
        if request.FILES:
            new_img = request.FILES[u'files[]']
            if new_img.size > settings.SALE_IMG_UPLOAD_MAX_SIZE:
                content = {'status': 'max_limit_error'}
                return HttpResponse(json.dumps(content), mimetype='application/json')

            new_media = EmailTemplateImage(image=request.FILES[u'files[]'])
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

