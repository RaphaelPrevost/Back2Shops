from django import template
from shippings.models import SC_FLAT_RATE

register = template.Library()


@register.simple_tag
@register.filter
def is_flat_rate(calculation_method):
    return (str(calculation_method).isdigit() and
            int(calculation_method) == SC_FLAT_RATE)

