from django import template
from shippings.models import SC_FREE_SHIPPING

register = template.Library()

@register.simple_tag
@register.filter
def is_free_shipping(calculation_method):

    return (str(calculation_method).isdigit() and
            int(calculation_method) == SC_FREE_SHIPPING)

