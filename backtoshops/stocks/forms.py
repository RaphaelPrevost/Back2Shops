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


from django import forms
from django.forms.formsets import formset_factory
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

class StockForm(forms.Form):
    sale_id = forms.IntegerField(widget=forms.HiddenInput())
    shop_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    ba_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    ca_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    stock = forms.IntegerField(required=False)

    sale_cover = forms.CharField(required=False)
    product_name = forms.CharField(required=False)
    ba_name = forms.CharField(required=False)
    ca_name = forms.CharField(required=False)
    sku = forms.CharField(required=False)
    barcode = forms.CharField(required=False)
    alert = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'is_required'}))

    def clean_stock(self):
        data = self.cleaned_data['stock']
        if not data:
            return None
        try:
            int_data = int(data)
        except:
            raise forms.ValidationError(_('Invalid stock quantity.'))
        return int_data


class StockListForm(forms.Form):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False):
        super(StockListForm, self).__init__(data, files, auto_id, prefix, initial,
                                            error_class, label_suffix, empty_permitted)
        StockFormset = formset_factory(StockForm, extra=0, can_delete=True)
        self.stocks = StockFormset(data=data, prefix="stocks",
                                   initial=initial)

    def clean(self):
        if self.stocks.errors:
            for form in self.stocks.forms:
                if form.errors:
                    raise forms.ValidationError(form.errors)
        return super(StockListForm, self).clean()

