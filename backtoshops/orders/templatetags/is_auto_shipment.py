from django import template
from B2SProtocol.constants import SHIPPING_CALCULATION_METHODS as SCM

register = template.Library()

@register.simple_tag
@register.filter
def is_auto_shipment(method):
    return int(method) in [SCM.CARRIER_SHIPPING_RATE,
                           SCM.CUSTOM_SHIPPING_RATE,
                           SCM.FREE_SHIPPING]
