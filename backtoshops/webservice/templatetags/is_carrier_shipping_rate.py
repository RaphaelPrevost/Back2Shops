from django import template
from shippings.models import SC_CARRIER_SHIPPING_RATE

register = template.Library()

@register.simple_tag
@register.filter
def is_carrier_shipping_rate(calculation_method):
    return int(calculation_method) == SC_CARRIER_SHIPPING_RATE
