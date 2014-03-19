from django import template
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM

register = template.Library()

@register.simple_tag
@register.filter
def is_manual_shipment(method):
    return int(method) == SCM.MANUAL
