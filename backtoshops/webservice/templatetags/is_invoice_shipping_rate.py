from django import template
from shippings.models import SC_INVOICE

register = template.Library()

@register.simple_tag
@register.filter
def is_invoice_shipping_rate(calculation_method):
    return int(calculation_method) == SC_INVOICE
