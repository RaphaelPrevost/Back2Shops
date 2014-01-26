from django import template
from shippings.models import SC_CUSTOM_SHIPPING_RATE

register = template.Library()

@register.filter
def is_custom_shipping_rate(calculation_method):
    return int(calculation_method) == SC_CUSTOM_SHIPPING_RATE
