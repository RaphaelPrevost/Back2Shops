from django import template
from B2SProtocol.constants import ORDER_STATUS

register = template.Library()

@register.simple_tag
@register.filter
def is_order_waiting_payment(status):
    return int(status) == ORDER_STATUS.AWAITING_PAYMENT
