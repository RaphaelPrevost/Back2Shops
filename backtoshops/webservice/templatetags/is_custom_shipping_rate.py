from django import template
from shippings.models import SC_CUSTOM_SHIPPING_RATE

register = template.Library()

@register.simple_tag
@register.filter
def is_custom_shipping_rate(calculation_method):
    return (str(calculation_method).isdigit() and
            int(calculation_method) == SC_CUSTOM_SHIPPING_RATE)
