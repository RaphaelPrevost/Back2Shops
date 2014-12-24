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


from django import forms
from django.utils.translation import ugettext_lazy as _
from routes.models import HtmlMeta, Route, RouteParam


class HTMLMetasForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'inputM'}))
    value = forms.CharField(widget=forms.TextInput(attrs={'class': 'inputL'}))

    class Meta:
        model = HtmlMeta


class RouteParamForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'inputM'}))
    is_required = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'is_required'}))

    class Meta:
        model = RouteParam

    def __init__(self, request=None, *args, **kwargs):
        super(RouteParamForm, self).__init__(*args, **kwargs)
        self.fields['is_required'].initial = False


class RouteForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    page_type = forms.CharField()
    page_role = forms.CharField()
    title = forms.CharField(required=False, label=_("HTML Title"))
    url_format = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    class Meta:
        model = Route
        exclude = ('mother_brand')

    def __init__(self, request=None, *args, **kwargs):
        super(RouteForm, self).__init__(*args, **kwargs)
        self.request = request

        # populate redirects field
        mother_brand_id = self.request.user.get_profile().work_for
        route_id = self.initial.get('id')

        # remove initial slash
        if self.initial.get('url_format', ' ')[0] == '/':
            self.initial['url_format'] = self.initial['url_format'][1:]

        # populate the routes
        datas = [(x.pk, x.page_type) for x in Route.objects.filter(mother_brand_id=mother_brand_id).exclude(id=route_id)]
        datas = [('', '---------')] + datas
        self.fields['redirects_to'].choices = datas

    def edit(self, request=None, *args,  **kwargs):
        raise Exception('edit')

    def save(self, commit=True):
        route = super(RouteForm, self).save(commit=False)
        route.mother_brand = self.request.user.get_profile().work_for

        # append slash if not exists
        if route.url_format[0] != '/':
            route.url_format = '/' + route.url_format

        if commit:
            route.save()

        return route
