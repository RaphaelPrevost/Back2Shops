from datetime import datetime
from itertools import chain
from django import forms
from django.forms.widgets import CheckboxInput
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from promotion.models import Group, TypesInGroup, SalesInGroup
from sales.models import STOCK_TYPE_DETAILED
from sales.models import ProductType
from sales.models import Sale
from shops.models import Shop


class CustomSalesCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def __init__(self, custom_initial, *args, **kwargs):
        super(CustomSalesCheckboxSelectMultiple, self).__init__(
            *args, **kwargs)
        self.custom_initial = custom_initial

    def _sale_attrs(self, id_sale):
        for sale in self.custom_initial:
            if int(sale.pk) == int(id_sale):
                return (sale.product.type_id,
                        (sale.type_stock == STOCK_TYPE_DETAILED and
                         [str(sp.pk) for sp in sale.shops.all()]
                         or []),
                        sale.product.name)

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = ['<ul>']
        # Normalize to strings
        str_values = set([force_text(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):

            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = format_html(' for="{0}"', final_attrs['id'])
            else:
                label_for = ''

            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_text(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = force_text(option_label)
            attr_type, attr_shops, sale_name = self._sale_attrs(option_value)
            option_label = ': '.join([sale_name, option_label])
            # 0 is for internet sales.
            shops = ','.join(attr_shops)
            output.append(format_html(
                '<li product_type={0} shops={1}><label{2}>{3} {4}</label></li>',
                attr_type, shops, label_for, rendered_cb, option_label))
        output.append('</ul>')
        return mark_safe('\n'.join(output))

class GroupForm(forms.Form):

    def __init__(self, instance=None, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.brand = kwargs['initial'].get('brand')
        self.orig_type_choices = kwargs['initial'].get('type_choices', [])
        self.orig_sales_choices = kwargs['initial'].get('sales_choices', [])
        self.pk = kwargs['initial'].get('pk', None)

        types = kwargs['initial'].get('types', [])
        sales = kwargs['initial'].get('sales', [])
        global_priority = kwargs['initial']['global_priority']

        self.fields['name'] = forms.CharField(
            required=True,
            label=_("Group Name"),
            initial=kwargs['initial'].get('name'),
            widget=forms.TextInput(
                attrs={'class': 'inputM'}))

        self.fields['types'] = forms.ModelMultipleChoiceField(
            label=_("Product Types"),
            required=True,
            queryset=types,
            widget=forms.CheckboxSelectMultiple(
                attrs={'class': 'checkbox'}))

        self.fields['sales'] = forms.ModelMultipleChoiceField(
            label=_("Sales"),
            required=True,
            queryset=sales,
            widget=CustomSalesCheckboxSelectMultiple(
                sales,
                attrs={'class': 'checkbox'}))

        self.fields['shop'] = forms.ModelChoiceField(
            label=_("Shops"),
            required=False,
            empty_label=_("Sales in global market") if global_priority else None,
            initial=kwargs['initial'].get('shop'),
            queryset=kwargs['initial'].get('shops'))


        self.initial['types'] = [t.pk for t in self.orig_type_choices]
        self.initial['sales'] = [s.pk for s in self.orig_sales_choices]

    def _create(self):
        group = Group.objects.create(
            name=self.cleaned_data['name'],
            shop=self.cleaned_data['shop'],
            brand=self.brand,
        )
        group.save()

        for type_  in self.cleaned_data['types']:
            type_in_group = TypesInGroup.objects.create(
                group=group,
                type=type_
            )
            type_in_group.save()

        for sale in self.cleaned_data['sales']:
            sale_in_group = SalesInGroup.objects.create(
                group=group,
                sale=sale
            )
            sale_in_group.save()

    def update(self):
        group = Group.objects.get(pk=self.pk)
        group.name=self.cleaned_data['name']
        group.shop=self.cleaned_data['shop']
        group.brand=self.brand
        group.updated=datetime.now()
        group.save()

        cur_types = set(self.cleaned_data['types'])
        for type_ in set(self.orig_type_choices) - set(cur_types):
            TypesInGroup.objects.get(
                type=type_,
                group=group,
            ).delete()

        for type_ in set(cur_types) - set(self.orig_type_choices):
            type_in_group = TypesInGroup.objects.create(
                type=type_,
                group=group
            )
            type_in_group.save()

        cur_sales = set(self.cleaned_data['sales'])
        for sale in set(self.orig_sales_choices) - set(cur_sales):
            SalesInGroup.objects.get(
                sale=sale,
                group=group
            ).delete()


        for sale in set(cur_sales) - set(self.orig_sales_choices):
            sale_in_group = SalesInGroup.objects.create(
                group=group,
                sale=sale
            )
            sale_in_group.save()

    def save(self):
        if not self.pk:
            return self._create()
        else:
            return self.update()

