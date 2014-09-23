from django import forms
from orders.models import Shipping
from django.utils.translation import ugettext_lazy as _
from shippings.models import Carrier, Service
from B2SProtocol.constants import ORDER_STATUS


class ShippingForm(forms.ModelForm):
    error_css_class = 'error'
    required_css_class = 'required'
    class Meta:
        model = Shipping

    def __init__(self, *args, **kwargs):
        super(ShippingForm, self).__init__(*args, **kwargs)
        self.fields['addr_dest'] = forms.CharField(
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
        self.fields['addr_orig'] = forms.CharField(
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))

        self.fields['weight'].widget = forms.TextInput(attrs={'class': 'input_weight'})
        self.fields['handling_fee'].widget = forms.TextInput(attrs={'class': 'input_handling_fee'})
        self.fields['ship_and_handling_fee'].widget = forms.TextInput(attrs={'class': 'input_handling_fee'})
        self.fields['shipment'] = forms.CharField(
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
        self.fields['total_fee'] = forms.CharField(
            widget=forms.TextInput(attrs={'readonly': 'readonly'}))

        self.fields['carrier'] = forms.ModelChoiceField(
            label=_('Carrier'),
            queryset=Carrier.objects.all(),
            empty_label=_("Please select a carrier"),
            widget=forms.widgets.Select(attrs={'readonly': 'readonly'})
        )
        self.fields['service'] = forms.ModelChoiceField(
            label=_('Services'),
            queryset=Service.objects.all(),
            empty_label=_("Please select a Service"),
            widget=forms.widgets.Select(attrs={'readonly': 'readonly'})
        )


class ListOrdersForm(forms.Form):
    ORDER_BY_ITEMS = [
        ('', "---" * 3),
        ('confirmation_time', _("Order creation time")),
        ('shop_ids', _("Shop")),
        ('carrier_ids', _("Carrier")),
    ]
    ORDER_BY_ITEMS_AFTER_PAYMENT = [
        ('shipping_deadline', _("Order deadline")),
    ]
    status = forms.IntegerField(widget=forms.HiddenInput())
    order_by1 = forms.ChoiceField(required=False, choices=ORDER_BY_ITEMS)
    order_by2 = forms.ChoiceField(required=False, choices=ORDER_BY_ITEMS)

    def __init__(self, status, *args, **kwargs):
        super(ListOrdersForm, self).__init__(*args, **kwargs)
        if status > ORDER_STATUS.AWAITING_PAYMENT:
            choices = self.ORDER_BY_ITEMS + self.ORDER_BY_ITEMS_AFTER_PAYMENT
            self.fields['order_by1'] = forms.ChoiceField(
                                       required=False, choices=choices,
                                       initial=kwargs.get('order_by1'))
            self.fields['order_by2'] = forms.ChoiceField(
                                       required=False, choices=choices,
                                       initial=kwargs.get('order_by2'))

