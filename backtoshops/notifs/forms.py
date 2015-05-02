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
from django.utils.translation import ugettext_lazy as _
from common.constants import NOTIF_DELIVERY_METHOD
from events.models import Event
from notifs.models import Notif

class NotifForm(forms.ModelForm):
    class Meta:
        model = Notif
        exclude = ('event', 'mother_brand', )

    def __init__(self, request=None, *args, **kwargs):
        super(NotifForm, self).__init__(*args, **kwargs)
        self.request = request
        initial = kwargs.get('initial') or {}
        instance = kwargs.get('instance') or None

        if instance:
            self.fields['event_id'] = forms.ChoiceField(
                    label=_("Event"),
                    choices=[(s.id, s.name)
                             for s in Event.objects.filter(pk=instance.event.id)])
        else:
            self.fields['event_id'] = forms.ChoiceField(
                    label=_("Event"),
                    choices=[(s.id, s.name) for s in Event.objects.all()])
        self.fields['delivery_method'] = forms.ChoiceField(
                label=_("Delivery"),
                choices=[(v, k) for k, v in NOTIF_DELIVERY_METHOD.toDict().iteritems()],
                initial=NOTIF_DELIVERY_METHOD.EMAIL)

        self.fields['html_head'] = forms.CharField(
                widget=forms.Textarea(attrs={'rows': '20'}),
                required=False,
                initial=
            '<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\n'
            '<meta content="width=device-width"/>')
        self.fields['html_body'] = forms.CharField(
                widget=forms.HiddenInput(),
                required=False)
        self.fields['params'] = forms.CharField(
                widget=forms.HiddenInput(),
                required=False)

        formset = formset_factory(NotifTemplateImageForm, extra=0, can_delete=True)
        if initial:
            self.images = formset(data=kwargs.get('data'),
                                  initial=initial.get('images', None),
                                  prefix="images")
        else:
            self.images = formset(data=kwargs.get('data'),
                                  prefix="images")

    def save(self, commit=True):
        notif = super(NotifForm, self).save(commit=False)
        notif.mother_brand = self.request.user.get_profile().work_for
        notif.event = Event.objects.get(pk=self.cleaned_data['event_id'])
        if commit:
            notif.save()
        return notif


class NotifTemplateImageForm(forms.Form):
    pk = forms.IntegerField(widget=forms.HiddenInput())
    url = forms.CharField(widget=forms.HiddenInput())
    thumb_url = forms.CharField(widget=forms.HiddenInput())

