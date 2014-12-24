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


import json
from django import forms
from django.forms.models import model_to_dict
from django.forms.models import fields_for_model
from django.utils.datastructures import SortedDict
from sales.models import ProductCurrency
from shops.models import Shop
from widgets import ScheduleWidget
from django.utils.translation import ugettext_lazy as _

from address.models import Address


class CountryField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
                return _(obj.printable_name)


class ScheduleField(forms.MultiValueField):
    widget = ScheduleWidget()

    def __init__(self, *args, **kwargs):
        fields = []
        for i in xrange(7*2*2):
            fields.append(forms.CharField())
        super(ScheduleField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        toret = SortedDict()
        if data_list:
            for i, j in enumerate(xrange(0, 7*2*2, 4)):
                toret[i] = {
                    'am': {'open': data_list[j], 'close': data_list[j+1]},
                    'pm': {'open': data_list[j+2], 'close': data_list[j+3]}
                }
        return json.dumps(toret)


class ShopForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'

    class Meta:
        model = Shop
        exclude = ("address",)

    def __init__(self, instance=None, *args, **kwargs):
        _fields = ('address', 'zipcode', 'city', 'country', 'province_code')
        _initial = model_to_dict(instance.address, _fields) if instance is not None else {}

        widgets = {
            'zipcode': forms.TextInput(attrs={'class': 'inputXS'}),
            'city': forms.TextInput(attrs={'class': 'inputM'}),
            #'country': CountryField(queryset=Country.objects.all(), empty_label=_('Select a country'), to_field_name='country'),
            'province_code': forms.HiddenInput()
        }
        kwargs['initial'].update(_initial)
        super(ShopForm, self).__init__(instance=instance, *args, **kwargs)
        self.fields.update(fields_for_model(Address, _fields, widgets=widgets))
        self.fields['upc'].widget = forms.TextInput(attrs={'class': 'inputM'})
        self.fields['phone'].widget = forms.TextInput(attrs={'class': 'inputS'})
        self.fields['description'].widget = forms.Textarea(attrs={"cols": 30, "rows": 4})
        self.fields['latitude'].widget = forms.HiddenInput()
        self.fields['longitude'].widget = forms.HiddenInput()
        self.fields['mother_brand'].widget = forms.HiddenInput()
        self.fields['opening_hours'] = ScheduleField(required=False)
        self.fields['business_reg_num'].widget = forms.TextInput(attrs={'class': 'inputM'})
        self.fields['tax_reg_num'].widget = forms.TextInput(attrs={'class': 'inputM'})
        currency_choices = [('', '-' * 9)]
        currency_choices.extend([(s, s) for s in
                     ProductCurrency.objects.all().values_list('code', flat=True)])
        self.fields['default_currency'] = forms.ChoiceField(
            choices=currency_choices, label=_('Default currency'),
            required=False)

    def save(self, *args, **kwargs):
        if self.instance.address_id:
            addr = self.instance.address
        else:
            addr = Address()
        addr.address = self.cleaned_data['address']
        addr.zipcode = self.cleaned_data['zipcode']
        addr.city = self.cleaned_data['city']
        addr.country = self.cleaned_data['country']
        addr.province_code = self.cleaned_data['province_code']
        addr.save()

        self.instance.address = addr
        shop = super(ShopForm, self).save(*args, **kwargs)
        return shop


