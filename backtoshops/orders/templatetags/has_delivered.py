from django import template
from B2SProtocol.constants import SHIPMENT_STATUS

register = template.Library()

@register.simple_tag
@register.filter
def has_delivered(status):
    return int(status) == SHIPMENT_STATUS.DELIVER
